from flask import Blueprint, jsonify, request
# Fix the import path
from models.repository import Repository
import concurrent.futures
from time import time

# Create blueprint for API routes
api_blueprint = Blueprint('api', __name__, url_prefix='/api')

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({"status": "ok", "message": "API is running"})

@api_blueprint.route('/repository/<path:repo_name>', methods=['GET'])
def get_repository(repo_name):
    """
    Get repository overview data.
    
    Args:
        repo_name (str): Repository name in format "owner/repo"
    """
    try:
        repo = Repository(repo_name)
        data = repo.fetch_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@api_blueprint.route('/repository/<path:repo_name>/commits', methods=['GET'])
def get_commit_analysis(repo_name):
    """
    Get commit analysis for a repository.
    
    Args:
        repo_name (str): Repository name in format "owner/repo"
    """
    try:
        days = request.args.get('days', default=30, type=int)
        repo = Repository(repo_name)
        data = repo.get_commit_trends(days=days)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@api_blueprint.route('/repository/<path:repo_name>/issues', methods=['GET'])
def get_issue_analysis(repo_name):
    """
    Get issue metrics for a repository.
    
    Args:
        repo_name (str): Repository name in format "owner/repo"
    """
    try:
        repo = Repository(repo_name)
        data = repo.get_issue_metrics()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@api_blueprint.route('/repository/<path:repo_name>/languages', methods=['GET'])
def get_language_analysis(repo_name):
    """
    Get language distribution for a repository.
    
    Args:
        repo_name (str): Repository name in format "owner/repo"
    """
    try:
        repo = Repository(repo_name)
        data = repo.get_language_analysis()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@api_blueprint.route('/analyze', methods=['POST'])
def analyze_repository():
    """
    Analyze a repository based on posted data.
    
    Expected request body:
    {
        "repo_name": "owner/repo"
    }
    """
    try:
        start_time = time()
        data = request.get_json()
        
        if not data or 'repo_name' not in data:
            return jsonify({"error": "Repository name is required"}), 400
        
        repo_name = data['repo_name']
        repo = Repository(repo_name)
        
        # Create a ThreadPoolExecutor to fetch data in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all the analysis tasks
            overview_future = executor.submit(repo.fetch_data)
            commits_future = executor.submit(repo.get_commit_trends)
            issues_future = executor.submit(repo.get_issue_metrics)
            languages_future = executor.submit(repo.get_language_analysis)
            
            # Get all results - this will block until all are complete
            # If any task raises an exception, it will be raised when the result is accessed
            overview = overview_future.result()
            commits = commits_future.result()
            issues = issues_future.result()
            languages = languages_future.result()
        
        # Combine all data
        result = {
            "overview": overview,
            "commits": commits,
            "issues": issues,
            "languages": languages,
            "analysis_time": round(time() - start_time, 2)  # Add analysis time for tracking
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500