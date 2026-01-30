import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class WeChatNotifier:
    """Sends notifications to WeChat Work webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_notification(self, changes: Dict[str, Any]) -> bool:
        """
        Send notification about repository changes.
        
        Args:
            changes: Dictionary containing change information with keys:
                - github_new_repos: List of new GitHub repos
                - github_updated_repos: List of repos with new commits
                - huggingface_new_models: List of new HuggingFace models
                - huggingface_updated_models: List of updated models
        
        Returns:
            True if sent successfully, False otherwise
        """
        message = self._format_message(changes)
        
        if not message:
            logger.debug("No changes to notify")
            return True
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": message
            }
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    logger.info("Notification sent successfully")
                    return True
                else:
                    logger.error(f"WeChat API error: {result}")
                    return False
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _format_message(self, changes: Dict[str, Any]) -> str:
        """Format changes into markdown message."""
        sections = []
        
        # GitHub new repos
        if changes.get("github_new_repos"):
            section = "## 🆕 New GitHub Repositories\n"
            for repo in changes["github_new_repos"]:
                org = repo.get('org', '')
                org_prefix = f"[{org}] " if org else ""
                section += f"- {org_prefix}[{repo['name']}]({repo['url']})\n"
            sections.append(section)
        
        # GitHub updated repos with commit details
        if changes.get("github_updated_repos"):
            section = "## 📝 GitHub Repository Updates\n"
            for repo in changes["github_updated_repos"]:
                org = repo.get('org', '')
                org_prefix = f"[{org}] " if org else ""
                commit = repo.get('commit', {})
                
                # Format: [org] repo_name: commit_sha - message (author)
                commit_sha = commit.get('sha', 'unknown')
                commit_msg = commit.get('message', 'No message')
                commit_author = commit.get('author', 'Unknown')
                
                section += f"- {org_prefix}[{repo['name']}]({repo['url']})\n"
                section += f"  `{commit_sha}` {commit_msg} *by {commit_author}*\n"
            sections.append(section)
        
        # HuggingFace new models
        if changes.get("huggingface_new_models"):
            section = "## 🤗 New HuggingFace Models\n"
            for model in changes["huggingface_new_models"]:
                section += f"- [{model['name']}]({model['url']})\n"
            sections.append(section)
        
        # HuggingFace updated models
        if changes.get("huggingface_updated_models"):
            section = "## 🔄 HuggingFace Model Updates\n"
            for model in changes["huggingface_updated_models"]:
                section += f"- [{model['name']}]({model['url']})\n"
            sections.append(section)
        
        # HuggingFace new datasets
        if changes.get("huggingface_new_datasets"):
            section = "## 🗂️ New HuggingFace Datasets\n"
            for dataset in changes["huggingface_new_datasets"]:
                section += f"- [{dataset['name']}]({dataset['url']})\n"
            sections.append(section)
        
        # HuggingFace updated datasets
        if changes.get("huggingface_updated_datasets"):
            section = "## 🔄 HuggingFace Dataset Updates\n"
            for dataset in changes["huggingface_updated_datasets"]:
                section += f"- [{dataset['name']}]({dataset['url']})\n"
            sections.append(section)
        
        return "\n".join(sections) if sections else ""
