import os
import pandas as pd
from github import Github
from github.GithubException import GithubException, BadCredentialsException, RateLimitExceededException
from datetime import datetime, timedelta
from utils.cache import cache


class GitHubAnalyzer:
    """Utility class to interact with GitHub API and analyze repositories."""
    
    def __init__(self, token=None):
        """Initialize GitHub connection with token."""
        if token is None:
            token = os.environ.get("GITHUB_TOKEN")
        
        if not token:
            raise ValueError("GitHub token is required. Please set GITHUB_TOKEN in your .env file.")
        
        try:
            # Configure Github with increased per_page and retry settings
            self.github = Github(token, per_page=100, retry=3)
            # Test the token with a simple API call
            self.github.get_user().login
        except BadCredentialsException:
            raise ValueError("Invalid GitHub token. Please check your token and ensure it has the necessary permissions.")
        except Exception as e:
            raise ValueError(f"Error initializing GitHub API client: {e}")
    
    def _get_from_cache(self, method_name, repo_name, **kwargs):
        """Get data from cache if available."""
        cache_key = cache.generate_key(method_name, repo_name, **kwargs)
        return cache.get(cache_key), cache_key
    
    def _save_to_cache(self, cache_key, data, expire_minutes=60):
        """Save data to cache."""
        cache.set(cache_key, data, expire_minutes)
    
    def get_repository(self, repo_name):
        """
        Fetch repository information.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
        
        Returns:
            dict: Repository information
        """
        cached_data, cache_key = self._get_from_cache('get_repository', repo_name)
        if cached_data:
            return cached_data
            
        try:
            repo = self.github.get_repo(repo_name)
            result = {
                "name": repo.name,
                "full_name": repo.full_name,
                "owner": repo.owner.login,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "language": repo.language,
            }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            return result
            
        except RateLimitExceededException as e:
            reset_time = self.github.rate_limiting_resettime
            wait_minutes = (reset_time - datetime.now().timestamp()) / 60
            raise Exception(f"GitHub API rate limit exceeded. Please try again in {wait_minutes:.1f} minutes.")
        except GithubException as e:
            raise Exception(f"Error fetching repository: {e}")
    
    def get_contributors(self, repo_name, limit=10):
        """
        Get top contributors for a repository.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
            limit (int): Maximum number of contributors to return
            
        Returns:
            list: List of contributors with their stats
        """
        cached_data, cache_key = self._get_from_cache('get_contributors', repo_name, limit=limit)
        if cached_data:
            return cached_data
        
        try:
            repo = self.github.get_repo(repo_name)
            contributors = repo.get_contributors()
            
            result = []
            for contributor in contributors[:limit]:
                result.append({
                    "login": contributor.login,
                    "id": contributor.id,
                    "contributions": contributor.contributions,
                    "url": contributor.html_url,
                    "avatar_url": contributor.avatar_url,
                })
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            return result
        except RateLimitExceededException as e:
            reset_time = self.github.rate_limiting_resettime
            wait_minutes = (reset_time - datetime.now().timestamp()) / 60
            raise Exception(f"GitHub API rate limit exceeded. Please try again in {wait_minutes:.1f} minutes.")
        except GithubException as e:
            raise Exception(f"Error fetching contributors: {e}")
    
    def get_commit_activity(self, repo_name, days=30, sample_size=500):
        """
        Get commit activity for a repository.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
            days (int): Number of days to analyze
            sample_size (int): Maximum number of commits to analyze for large repos
            
        Returns:
            dict: Commit activity data
        """
        cached_data, cache_key = self._get_from_cache('get_commit_activity', repo_name, days=days)
        if cached_data:
            return cached_data
        
        try:
            repo = self.github.get_repo(repo_name)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get commits in date range
            commits = repo.get_commits(since=start_date, until=end_date)
            
            # Check if repository has too many commits
            total_count = 0
            is_sampled = False
            try:
                total_count = commits.totalCount
                is_sampled = total_count > sample_size
            except:
                # If we can't get total count, proceed with sampling
                is_sampled = True
                
            # Process commits - with sampling for large repos
            commit_data = []
            sampling_factor = 1
            
            if is_sampled:
                # Estimate how many commits to skip
                try:
                    sampling_factor = max(1, total_count // sample_size)
                except:
                    sampling_factor = 5  # Default if we can't calculate
                
                count = 0
                for commit in commits:
                    if count % sampling_factor == 0:  # Sample every Nth commit
                        commit_data.append({
                            "sha": commit.sha,
                            "author": commit.author.login if commit.author else "Unknown",
                            "date": commit.commit.author.date.isoformat(),
                            "message": commit.commit.message,
                        })
                    count += 1
                    if len(commit_data) >= sample_size:
                        break
            else:
                # Get all commits for smaller repos
                for commit in commits:
                    commit_data.append({
                        "sha": commit.sha,
                        "author": commit.author.login if commit.author else "Unknown",
                        "date": commit.commit.author.date.isoformat(),
                        "message": commit.commit.message,
                    })
            
            # Create DataFrame for analysis
            df = pd.DataFrame(commit_data)
            
            # Only proceed if we have commits
            if len(df) == 0:
                result = {
                    "total_commits": 0,
                    "daily_commits": [],
                    "authors": [],
                    "is_sampled": False,
                    "sampling_factor": 1
                }
                self._save_to_cache(cache_key, result)
                return result
            
            # Extract date from datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
                
                # Daily commit counts
                daily_commits = df.groupby('date').size().reset_index()
                daily_commits.columns = ['date', 'count']
                
                # Adjust counts if sampled
                if is_sampled:
                    daily_commits['count'] = daily_commits['count'] * sampling_factor
                
                # Author stats
                author_stats = df.groupby('author').size().reset_index()
                author_stats.columns = ['author', 'count']
                
                # Adjust counts if sampled
                if is_sampled:
                    author_stats['count'] = author_stats['count'] * sampling_factor
                    
                author_stats = author_stats.sort_values('count', ascending=False)
                
                result = {
                    "total_commits": total_count if is_sampled else len(df),
                    "daily_commits": daily_commits.to_dict('records'),
                    "authors": author_stats.to_dict('records'),
                    "is_sampled": is_sampled,
                    "sampling_factor": sampling_factor
                }
                self._save_to_cache(cache_key, result)
                return result
            else:
                result = {
                    "total_commits": 0,
                    "daily_commits": [],
                    "authors": [],
                    "is_sampled": False,
                    "sampling_factor": 1
                }
                self._save_to_cache(cache_key, result)
                return result
        except RateLimitExceededException as e:
            reset_time = self.github.rate_limiting_resettime
            wait_minutes = (reset_time - datetime.now().timestamp()) / 60
            raise Exception(f"GitHub API rate limit exceeded. Please try again in {wait_minutes:.1f} minutes.")
        except GithubException as e:
            raise Exception(f"Error analyzing commit activity: {e}")
    
    def get_issues_analysis(self, repo_name, max_issues=100):
        """
        Analyze issues for a repository.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
            max_issues (int): Maximum number of issues to analyze
            
        Returns:
            dict: Issue analysis data
        """
        cached_data, cache_key = self._get_from_cache('get_issues_analysis', repo_name, max_issues=max_issues)
        if cached_data:
            return cached_data
        
        try:
            repo = self.github.get_repo(repo_name)
            
            # Get open and closed issues
            try:
                open_issues = repo.get_issues(state='open')
                open_issues_count = open_issues.totalCount
            except Exception:
                open_issues = []
                open_issues_count = 0
                
            try:
                closed_issues = repo.get_issues(state='closed')
                closed_issues_count = closed_issues.totalCount
            except Exception:
                closed_issues = []
                closed_issues_count = 0
            
            # Process open issues
            open_issues_data = []
            try:
                # Determine if we need to sample
                is_sampled = open_issues_count > max_issues
                sampling_factor = max(1, open_issues_count // max_issues) if is_sampled else 1
                
                count = 0
                for issue in open_issues:
                    # Sample if needed
                    if count % sampling_factor == 0:
                        try:
                            open_issues_data.append({
                                "number": issue.number,
                                "title": issue.title,
                                "state": issue.state,
                                "created_at": issue.created_at.isoformat(),
                                "updated_at": issue.updated_at.isoformat(),
                                "user": issue.user.login if issue.user else "Unknown",
                            })
                        except Exception:
                            # Skip problematic issues
                            pass
                    
                    count += 1
                    if len(open_issues_data) >= max_issues:
                        break
            except Exception:
                # If any error occurs processing open issues, continue with empty list
                pass
            
            # Process closed issues
            closed_issues_data = []
            try:
                # Determine if we need to sample
                is_sampled = closed_issues_count > max_issues
                sampling_factor = max(1, closed_issues_count // max_issues) if is_sampled else 1
                
                count = 0
                for issue in closed_issues:
                    # Sample if needed
                    if count % sampling_factor == 0:
                        try:
                            closed_issues_data.append({
                                "number": issue.number,
                                "title": issue.title,
                                "state": issue.state,
                                "created_at": issue.created_at.isoformat(),
                                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                                "user": issue.user.login if issue.user else "Unknown",
                            })
                        except Exception:
                            # Skip problematic issues
                            pass
                    
                    count += 1
                    if len(closed_issues_data) >= max_issues:
                        break
            except Exception:
                # If any error occurs processing closed issues, continue with empty list
                pass
            
            result = {
                "open_issues_count": open_issues_count,
                "closed_issues_count": closed_issues_count,
                "open_issues": open_issues_data,
                "closed_issues": closed_issues_data,
            }
            self._save_to_cache(cache_key, result)
            return result
        except RateLimitExceededException as e:
            reset_time = self.github.rate_limiting_resettime
            wait_minutes = (reset_time - datetime.now().timestamp()) / 60
            raise Exception(f"GitHub API rate limit exceeded. Please try again in {wait_minutes:.1f} minutes.")
        except GithubException as e:
            # For repositories with no issues or issues disabled
            if e.status == 404 or e.status == 410:
                result = {
                    "open_issues_count": 0,
                    "closed_issues_count": 0,
                    "open_issues": [],
                    "closed_issues": []
                }
                self._save_to_cache(cache_key, result)
                return result
            raise Exception(f"Error analyzing issues: {e}")
    
    def get_languages(self, repo_name):
        """
        Get language distribution for a repository.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
            
        Returns:
            dict: Language distribution data
        """
        cached_data, cache_key = self._get_from_cache('get_languages', repo_name)
        if cached_data:
            return cached_data
        
        try:
            repo = self.github.get_repo(repo_name)
            languages = repo.get_languages()
            
            total_bytes = sum(languages.values())
            
            # Calculate percentages
            language_stats = []
            for lang, bytes_count in languages.items():
                percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
                language_stats.append({
                    "language": lang,
                    "bytes": bytes_count,
                    "percentage": round(percentage, 2)
                })
            
            # Sort by percentage (descending)
            language_stats = sorted(language_stats, key=lambda x: x["percentage"], reverse=True)
            
            result = {
                "total_bytes": total_bytes,
                "languages": language_stats
            }
            self._save_to_cache(cache_key, result)
            return result
        except RateLimitExceededException as e:
            reset_time = self.github.rate_limiting_resettime
            wait_minutes = (reset_time - datetime.now().timestamp()) / 60
            raise Exception(f"GitHub API rate limit exceeded. Please try again in {wait_minutes:.1f} minutes.")
        except GithubException as e:
            raise Exception(f"Error fetching languages: {e}")
    
    def get_repository_overview(self, repo_name):
        """
        Get comprehensive overview of a repository.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
            
        Returns:
            dict: Repository overview data
        """
        cached_data, cache_key = self._get_from_cache('get_repository_overview', repo_name)
        if cached_data:
            return cached_data
        
        try:
            # Get basic repository info
            repo_info = self.get_repository(repo_name)
            
            # Get contributors
            contributors = self.get_contributors(repo_name, limit=5)
            
            # Get languages
            languages = self.get_languages(repo_name)
            
            # Get commit activity for last 30 days
            commit_activity = self.get_commit_activity(repo_name, days=30)
            
            # Combine all data
            overview = {
                "repository": repo_info,
                "contributors": contributors,
                "languages": languages,
                "commit_activity": commit_activity,
            }
            
            self._save_to_cache(cache_key, overview)
            return overview
        except Exception as e:
            raise Exception(f"Error generating repository overview: {e}")