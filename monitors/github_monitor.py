import logging
import requests
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubMonitor:
    """Monitors GitHub organization for repository and commit changes."""
    
    def __init__(self, org_name: str = "deepseek-ai", github_token: Optional[str] = None):
        self.org_name = org_name
        self.base_url = "https://api.github.com"
        self.headers = {}
        
        # Use provided GitHub token or check environment variable
        token = github_token or os.environ.get("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"token {token}"
            logger.info(f"Using GitHub token for {org_name} (5000 req/hour)")
        else:
            logger.info(f"No GitHub token for {org_name}, using unauthenticated API (60 req/hour)")
    
    def fetch_current_state(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current state of all repositories in the organization.
        
        Returns:
            Dictionary with repo data, or None if failed
        """
        try:
            # Fetch all repos in organization
            repos_url = f"{self.base_url}/orgs/{self.org_name}/repos"
            params = {"per_page": 100, "type": "all"}
            
            response = requests.get(repos_url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 403:
                logger.warning("GitHub rate limit reached, skipping this cycle")
                return None
            
            if response.status_code != 200:
                logger.error(f"GitHub API error {response.status_code}: {response.text}")
                return None
            
            repos = response.json()
            logger.info(f"Fetched {len(repos)} repositories from GitHub ({self.org_name})")
            
            # Build state with latest commit for each repo
            state = {
                "last_check": datetime.utcnow().isoformat() + "Z",
                "repos": {}
            }
            
            for repo in repos:
                repo_name = repo["name"]
                default_branch = repo.get("default_branch", "main")
                
                # Fetch latest commit SHA and details
                commit_info = self._fetch_latest_commit(repo_name, default_branch)
                
                # Always save repo info, even if commit fetch fails
                state["repos"][repo_name] = {
                    "id": repo["id"],
                    "url": repo["html_url"],
                    "default_branch": default_branch,
                    "last_commit": commit_info  # Dict with sha, message, author, date
                }
            
            return state
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching GitHub data: {e}")
            return None
    
    def detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare old and new states to detect changes based on commit SHA.
        
        Returns:
            Dictionary with 'new_repos' and 'updated_repos' lists
        """
        if not old_state or not old_state.get("repos"):
            # First run, no changes to report
            return {"new_repos": [], "updated_repos": []}
        
        old_repos = old_state.get("repos", {})
        new_repos_dict = new_state.get("repos", {})
        
        changes = {
            "new_repos": [],
            "updated_repos": []
        }
        
        # Detect new repositories
        for repo_name, repo_data in new_repos_dict.items():
            if repo_name not in old_repos:
                changes["new_repos"].append({
                    "name": repo_name,
                    "url": repo_data["url"],
                    "org": self.org_name
                })
                logger.info(f"New repository detected: {repo_name} ({self.org_name})")
        
        # Detect updated repositories (new commits based on SHA)
        for repo_name, repo_data in new_repos_dict.items():
            if repo_name in old_repos:
                old_commit = old_repos[repo_name].get("last_commit", {})
                new_commit = repo_data.get("last_commit", {})
                
                old_sha = old_commit.get("sha") if old_commit else None
                new_sha = new_commit.get("sha") if new_commit else None
                
                # Compare SHAs to detect real commits (not just pushed_at changes)
                if old_sha and new_sha and old_sha != new_sha:
                    changes["updated_repos"].append({
                        "name": repo_name,
                        "url": repo_data["url"],
                        "org": self.org_name,
                        "commit": {
                            "sha": new_sha[:7],  # Short SHA
                            "message": new_commit.get("message", "No message"),
                            "author": new_commit.get("author", "Unknown"),
                            "date": new_commit.get("date", "")
                        }
                    })
                    logger.info(f"New commit detected in {repo_name} ({self.org_name}): {new_sha[:7]} by {new_commit.get('author', 'Unknown')}")
        
        return changes
    
    def _fetch_latest_commit(self, repo_name: str, branch: str) -> Optional[Dict[str, str]]:
        """
        Fetch the latest commit info for a specific repository and branch.
        
        Args:
            repo_name: Repository name
            branch: Branch name (e.g., "main", "master")
        
        Returns:
            Dict with commit info (sha, message, author, date) or None if failed
        """
        try:
            commits_url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits/{branch}"
            response = requests.get(commits_url, headers=self.headers, timeout=30)
            
            if response.status_code == 403:
                logger.debug(f"Rate limit hit when fetching commit for {repo_name}")
                return None
            
            if response.status_code == 404:
                logger.debug(f"Branch {branch} not found in {repo_name}, trying 'master'")
                # Try 'master' if 'main' doesn't exist
                if branch == "main":
                    return self._fetch_latest_commit(repo_name, "master")
                return None
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch commit for {repo_name}: {response.status_code}")
                return None
            
            commit_data = response.json()
            
            # Extract commit details
            sha = commit_data.get("sha", "")
            commit_info = commit_data.get("commit", {})
            message = commit_info.get("message", "").split("\n")[0]  # First line only
            author_info = commit_info.get("author", {})
            author = author_info.get("name", "Unknown")
            date = author_info.get("date", "")
            
            return {
                "sha": sha,
                "message": message,
                "author": author,
                "date": date
            }
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Network error fetching commit for {repo_name}: {e}")
            return None
