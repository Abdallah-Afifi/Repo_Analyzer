import json
from datetime import datetime, date
# Fix the import path
from utils.github_api import GitHubAnalyzer


class Repository:
    """Repository model class for handling repository data and analysis."""
    
    def __init__(self, repo_name):
        """
        Initialize a repository model.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
        """
        self.repo_name = repo_name
        self.analyzer = GitHubAnalyzer()
        self.data = None
    
    def fetch_data(self):
        """
        Fetch all repository data from GitHub API.
        
        Returns:
            dict: Repository data
        """
        try:
            self.data = self.analyzer.get_repository_overview(self.repo_name)
            return self.data
        except Exception as e:
            raise Exception(f"Error fetching repository data: {e}")
    
    def get_issue_metrics(self):
        """
        Get issue-related metrics.
        
        Returns:
            dict: Issue metrics
        """
        try:
            issues_data = self.analyzer.get_issues_analysis(self.repo_name)
            
            # Calculate metrics
            open_issues = issues_data.get("open_issues_count", 0)
            closed_issues = issues_data.get("closed_issues_count", 0)
            total_issues = open_issues + closed_issues
            
            # Calculate resolution rate
            resolution_rate = (closed_issues / total_issues * 100) if total_issues > 0 else 0
            
            return {
                "open_issues": open_issues,
                "closed_issues": closed_issues,
                "total_issues": total_issues,
                "resolution_rate": round(resolution_rate, 2)
            }
        except Exception as e:
            raise Exception(f"Error calculating issue metrics: {e}")
    
    def get_commit_trends(self, days=30):
        """
        Get commit trend analysis.
        
        Args:
            days (int): Number of days to analyze
            
        Returns:
            dict: Commit trend data
        """
        try:
            commit_data = self.analyzer.get_commit_activity(self.repo_name, days=days)
            
            # Extract commit counts by day
            daily_counts = []
            for day_data in commit_data.get("daily_commits", []):
                daily_counts.append({
                    "date": day_data["date"].isoformat() if isinstance(day_data["date"], date) else day_data["date"],
                    "count": day_data["count"]
                })
            
            # Get author contribution data
            author_data = commit_data.get("authors", [])
            
            # Calculate average commits per day
            avg_commits_per_day = commit_data["total_commits"] / days if days > 0 else 0
            
            return {
                "total_commits": commit_data["total_commits"],
                "daily_commits": daily_counts,
                "author_contributions": author_data,
                "avg_commits_per_day": round(avg_commits_per_day, 2)
            }
        except Exception as e:
            raise Exception(f"Error analyzing commit trends: {e}")
    
    def get_language_analysis(self):
        """
        Get language distribution analysis.
        
        Returns:
            dict: Language analysis data
        """
        try:
            language_data = self.analyzer.get_languages(self.repo_name)
            
            # Extract top languages
            top_languages = language_data.get("languages", [])[:5]
            
            # Calculate "other" category if there are more than 5 languages
            if len(language_data.get("languages", [])) > 5:
                other_percentage = sum(lang["percentage"] for lang in language_data.get("languages", [])[5:])
                other_bytes = sum(lang["bytes"] for lang in language_data.get("languages", [])[5:])
                
                top_languages.append({
                    "language": "Other",
                    "percentage": round(other_percentage, 2),
                    "bytes": other_bytes
                })
            
            return {
                "languages": top_languages,
                "total_bytes": language_data.get("total_bytes", 0)
            }
        except Exception as e:
            raise Exception(f"Error analyzing languages: {e}")
    
    def to_json(self):
        """
        Convert repository data to JSON.
        
        Returns:
            str: JSON representation of repository data
        """
        if self.data is None:
            self.fetch_data()
        
        return json.dumps(self.data, default=str)
    
    @classmethod
    def from_name(cls, repo_name):
        """
        Create a Repository instance from a repo name and fetch its data.
        
        Args:
            repo_name (str): Repository name in format "owner/repo"
            
        Returns:
            Repository: Repository instance with fetched data
        """
        repo = cls(repo_name)
        repo.fetch_data()
        return repo