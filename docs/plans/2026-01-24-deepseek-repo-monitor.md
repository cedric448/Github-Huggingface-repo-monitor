# DeepSeek Repository Monitor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python service that monitors DeepSeek's GitHub and HuggingFace repositories for changes and sends WeChat Work notifications.

**Architecture:** Containerized Python service with separate modules for GitHub/HuggingFace monitoring, JSON-based state persistence, and WeChat webhook notifications. Runs continuously with 60-second check intervals.

**Tech Stack:** Python 3.11, requests library, Docker, docker-compose

---

## Task 1: Project Structure and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create requirements.txt**

```bash
cat > requirements.txt << 'EOF'
requests==2.31.0
EOF
```

**Step 2: Create .gitignore**

```bash
cat > .gitignore << 'EOF'
# State files
state/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
.dockerignore

# Logs
*.log
EOF
```

**Step 3: Create README.md**

```bash
cat > README.md << 'EOF'
# DeepSeek Repository Monitor

Monitors DeepSeek's GitHub and HuggingFace repositories for changes and sends notifications via WeChat Work.

## Features

- Monitors GitHub organization: https://github.com/deepseek-ai
- Monitors HuggingFace organization: https://huggingface.co/deepseek-ai
- Detects new repositories and new commits
- Sends notifications via WeChat Work webhook
- Runs every 60 seconds
- State persisted in JSON files

## Setup

1. Configure webhook URL in `docker-compose.yml`
2. Build and run: `docker-compose up -d`
3. View logs: `docker-compose logs -f monitor`
4. Stop: `docker-compose down`

## State Files

State is stored in `./state/` directory:
- `github_state.json` - GitHub repos and commits
- `huggingface_state.json` - HuggingFace models and datasets
EOF
```

**Step 4: Create directory structure**

```bash
mkdir -p monitors utils tests
```

**Step 5: Commit**

```bash
git init
git add requirements.txt .gitignore README.md
git commit -m "chore: initial project structure"
```

---

## Task 2: State Manager

**Files:**
- Create: `utils/__init__.py`
- Create: `utils/state_manager.py`

**Step 1: Create utils/__init__.py**

```python
# Empty file for package
```

**Step 2: Create state_manager.py**

```python
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class StateManager:
    """Manages JSON state files for tracking repository changes."""
    
    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self._ensure_state_dir()
    
    def _ensure_state_dir(self) -> None:
        """Create state directory if it doesn't exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"State directory ready: {self.state_dir}")
    
    def load_state(self, filename: str) -> Dict[str, Any]:
        """
        Load state from JSON file.
        
        Args:
            filename: Name of the state file (e.g., 'github_state.json')
        
        Returns:
            Dictionary containing state, or empty dict if file doesn't exist
        """
        filepath = self.state_dir / filename
        
        if not filepath.exists():
            logger.info(f"State file not found: {filename}, starting fresh")
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            logger.info(f"Loaded state from {filename}")
            return state
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}, treating as fresh start")
            return {}
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}, treating as fresh start")
            return {}
    
    def save_state(self, filename: str, state: Dict[str, Any]) -> bool:
        """
        Save state to JSON file.
        
        Args:
            filename: Name of the state file
            state: Dictionary to save
        
        Returns:
            True if saved successfully, False otherwise
        """
        filepath = self.state_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved state to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            return False
```

**Step 3: Commit**

```bash
git add utils/
git commit -m "feat: add state manager for JSON persistence"
```

---

## Task 3: WeChat Notifier

**Files:**
- Create: `utils/wechat_notifier.py`

**Step 1: Create wechat_notifier.py**

```python
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
                section += f"- [{repo['name']}]({repo['url']})\n"
            sections.append(section)
        
        # GitHub updated repos
        if changes.get("github_updated_repos"):
            section = "## 📝 GitHub Repository Updates\n"
            for repo in changes["github_updated_repos"]:
                section += f"- [{repo['name']}]({repo['url']}): {repo['commit_count']} new commit(s)\n"
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
        
        return "\n".join(sections) if sections else ""
```

**Step 2: Commit**

```bash
git add utils/wechat_notifier.py
git commit -m "feat: add WeChat Work notifier with markdown formatting"
```

---

## Task 4: GitHub Monitor

**Files:**
- Create: `monitors/__init__.py`
- Create: `monitors/github_monitor.py`

**Step 1: Create monitors/__init__.py**

```python
# Empty file for package
```

**Step 2: Create github_monitor.py**

```python
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubMonitor:
    """Monitors GitHub organization for repository and commit changes."""
    
    def __init__(self, org_name: str = "deepseek-ai"):
        self.org_name = org_name
        self.base_url = "https://api.github.com"
    
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
            
            response = requests.get(repos_url, params=params, timeout=30)
            
            if response.status_code == 403:
                logger.warning("GitHub rate limit reached, skipping this cycle")
                return None
            
            if response.status_code != 200:
                logger.error(f"GitHub API error {response.status_code}: {response.text}")
                return None
            
            repos = response.json()
            logger.info(f"Fetched {len(repos)} repositories from GitHub")
            
            # Build state with latest commit for each repo
            state = {
                "last_check": datetime.utcnow().isoformat() + "Z",
                "repos": {}
            }
            
            for repo in repos:
                repo_name = repo["name"]
                default_branch = repo.get("default_branch", "main")
                
                # Fetch latest commit
                commit_sha = self._fetch_latest_commit(repo_name, default_branch)
                
                if commit_sha:
                    state["repos"][repo_name] = {
                        "id": repo["id"],
                        "url": repo["html_url"],
                        "default_branch": default_branch,
                        "last_commit_sha": commit_sha
                    }
            
            return state
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching GitHub data: {e}")
            return None
    
    def _fetch_latest_commit(self, repo_name: str, branch: str) -> Optional[str]:
        """Fetch the latest commit SHA for a repository branch."""
        try:
            commits_url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits"
            params = {"sha": branch, "per_page": 1}
            
            response = requests.get(commits_url, params=params, timeout=10)
            
            if response.status_code == 200:
                commits = response.json()
                if commits:
                    return commits[0]["sha"]
            else:
                logger.warning(f"Could not fetch commits for {repo_name}: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching commits for {repo_name}: {e}")
            return None
    
    def detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare old and new states to detect changes.
        
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
                    "url": repo_data["url"]
                })
                logger.info(f"New repository detected: {repo_name}")
        
        # Detect updated repositories (new commits)
        for repo_name, repo_data in new_repos_dict.items():
            if repo_name in old_repos:
                old_sha = old_repos[repo_name].get("last_commit_sha")
                new_sha = repo_data.get("last_commit_sha")
                
                if old_sha and new_sha and old_sha != new_sha:
                    # Count commits between old and new SHA
                    commit_count = self._count_commits_between(repo_name, old_sha, new_sha)
                    
                    changes["updated_repos"].append({
                        "name": repo_name,
                        "url": repo_data["url"],
                        "commit_count": commit_count
                    })
                    logger.info(f"Repository updated: {repo_name} ({commit_count} new commits)")
        
        return changes
    
    def _count_commits_between(self, repo_name: str, old_sha: str, new_sha: str) -> int:
        """Count commits between two SHAs."""
        try:
            compare_url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/compare/{old_sha}...{new_sha}"
            response = requests.get(compare_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("total_commits", 1)
            
            return 1  # Default to 1 if can't fetch
            
        except Exception as e:
            logger.warning(f"Error counting commits for {repo_name}: {e}")
            return 1
```

**Step 3: Commit**

```bash
git add monitors/
git commit -m "feat: add GitHub monitor for repos and commits"
```

---

## Task 5: HuggingFace Monitor

**Files:**
- Create: `monitors/huggingface_monitor.py`

**Step 1: Create huggingface_monitor.py**

```python
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HuggingFaceMonitor:
    """Monitors HuggingFace organization for model and dataset changes."""
    
    def __init__(self, org_name: str = "deepseek-ai"):
        self.org_name = org_name
        self.base_url = "https://huggingface.co/api"
    
    def fetch_current_state(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current state of all models and datasets.
        
        Returns:
            Dictionary with model/dataset data, or None if failed
        """
        try:
            state = {
                "last_check": datetime.utcnow().isoformat() + "Z",
                "models": {},
                "datasets": {}
            }
            
            # Fetch models
            models = self._fetch_models()
            if models is not None:
                for model in models:
                    model_id = model.get("id") or model.get("modelId")
                    if model_id:
                        state["models"][model_id] = {
                            "id": model_id,
                            "url": f"https://huggingface.co/{model_id}",
                            "last_modified": model.get("lastModified", "")
                        }
                logger.info(f"Fetched {len(state['models'])} models from HuggingFace")
            
            # Fetch datasets
            datasets = self._fetch_datasets()
            if datasets is not None:
                for dataset in datasets:
                    dataset_id = dataset.get("id")
                    if dataset_id:
                        state["datasets"][dataset_id] = {
                            "id": dataset_id,
                            "url": f"https://huggingface.co/datasets/{dataset_id}",
                            "last_modified": dataset.get("lastModified", "")
                        }
                logger.info(f"Fetched {len(state['datasets'])} datasets from HuggingFace")
            
            return state
            
        except Exception as e:
            logger.error(f"Error fetching HuggingFace data: {e}")
            return None
    
    def _fetch_models(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all models for the organization."""
        try:
            url = f"{self.base_url}/models"
            params = {"author": self.org_name, "limit": 500}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HuggingFace models API error {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching HuggingFace models: {e}")
            return None
    
    def _fetch_datasets(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all datasets for the organization."""
        try:
            url = f"{self.base_url}/datasets"
            params = {"author": self.org_name, "limit": 500}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HuggingFace datasets API error {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching HuggingFace datasets: {e}")
            return None
    
    def detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare old and new states to detect changes.
        
        Returns:
            Dictionary with 'new_models', 'updated_models', 'new_datasets', 'updated_datasets'
        """
        if not old_state or (not old_state.get("models") and not old_state.get("datasets")):
            # First run, no changes to report
            return {
                "new_models": [],
                "updated_models": [],
                "new_datasets": [],
                "updated_datasets": []
            }
        
        old_models = old_state.get("models", {})
        new_models = new_state.get("models", {})
        old_datasets = old_state.get("datasets", {})
        new_datasets = new_state.get("datasets", {})
        
        changes = {
            "new_models": [],
            "updated_models": [],
            "new_datasets": [],
            "updated_datasets": []
        }
        
        # Detect new models
        for model_id, model_data in new_models.items():
            if model_id not in old_models:
                changes["new_models"].append({
                    "name": model_id,
                    "url": model_data["url"]
                })
                logger.info(f"New model detected: {model_id}")
        
        # Detect updated models
        for model_id, model_data in new_models.items():
            if model_id in old_models:
                old_modified = old_models[model_id].get("last_modified", "")
                new_modified = model_data.get("last_modified", "")
                
                if old_modified and new_modified and old_modified != new_modified:
                    changes["updated_models"].append({
                        "name": model_id,
                        "url": model_data["url"]
                    })
                    logger.info(f"Model updated: {model_id}")
        
        # Detect new datasets
        for dataset_id, dataset_data in new_datasets.items():
            if dataset_id not in old_datasets:
                changes["new_datasets"].append({
                    "name": dataset_id,
                    "url": dataset_data["url"]
                })
                logger.info(f"New dataset detected: {dataset_id}")
        
        # Detect updated datasets
        for dataset_id, dataset_data in new_datasets.items():
            if dataset_id in old_datasets:
                old_modified = old_datasets[dataset_id].get("last_modified", "")
                new_modified = dataset_data.get("last_modified", "")
                
                if old_modified and new_modified and old_modified != new_modified:
                    changes["updated_datasets"].append({
                        "name": dataset_id,
                        "url": dataset_data["url"]
                    })
                    logger.info(f"Dataset updated: {dataset_id}")
        
        return changes
```

**Step 2: Commit**

```bash
git add monitors/huggingface_monitor.py
git commit -m "feat: add HuggingFace monitor for models and datasets"
```

---

## Task 6: Main Application

**Files:**
- Create: `main.py`
- Create: `config.py`

**Step 1: Create config.py**

```python
import os

# Configuration
WECHAT_WEBHOOK_URL = os.environ.get(
    "WECHAT_WEBHOOK_URL",
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e55bfcc3-4b1e-4656-8e70-7415d00f17f4"
)

CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))

GITHUB_ORG = "deepseek-ai"
HUGGINGFACE_ORG = "deepseek-ai"

STATE_DIR = "state"
GITHUB_STATE_FILE = "github_state.json"
HUGGINGFACE_STATE_FILE = "huggingface_state.json"
```

**Step 2: Create main.py**

```python
#!/usr/bin/env python3
import logging
import time
import signal
import sys
from typing import Dict, Any

from config import (
    WECHAT_WEBHOOK_URL,
    CHECK_INTERVAL,
    GITHUB_ORG,
    HUGGINGFACE_ORG,
    STATE_DIR,
    GITHUB_STATE_FILE,
    HUGGINGFACE_STATE_FILE
)
from utils.state_manager import StateManager
from utils.wechat_notifier import WeChatNotifier
from monitors.github_monitor import GitHubMonitor
from monitors.huggingface_monitor import HuggingFaceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global shutdown_flag
    logger.info("Received shutdown signal, stopping gracefully...")
    shutdown_flag = True


def main():
    """Main monitoring loop."""
    logger.info("DeepSeek Repository Monitor starting...")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"Monitoring GitHub org: {GITHUB_ORG}")
    logger.info(f"Monitoring HuggingFace org: {HUGGINGFACE_ORG}")
    
    # Initialize components
    state_manager = StateManager(STATE_DIR)
    notifier = WeChatNotifier(WECHAT_WEBHOOK_URL)
    github_monitor = GitHubMonitor(GITHUB_ORG)
    huggingface_monitor = HuggingFaceMonitor(HUGGINGFACE_ORG)
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load existing state
    github_state = state_manager.load_state(GITHUB_STATE_FILE)
    huggingface_state = state_manager.load_state(HUGGINGFACE_STATE_FILE)
    
    is_first_run = not github_state and not huggingface_state
    
    if is_first_run:
        logger.info("First run detected, will initialize state silently")
    
    logger.info("Starting monitoring loop...")
    
    while not shutdown_flag:
        cycle_start = time.time()
        
        try:
            # Check GitHub
            github_changes = check_github(
                github_monitor,
                state_manager,
                github_state,
                is_first_run
            )
            
            # Check HuggingFace
            huggingface_changes = check_huggingface(
                huggingface_monitor,
                state_manager,
                huggingface_state,
                is_first_run
            )
            
            # Send notification if there are changes and not first run
            if not is_first_run:
                all_changes = merge_changes(github_changes, huggingface_changes)
                if has_changes(all_changes):
                    notifier.send_notification(all_changes)
            
            # After first run, set flag to false
            if is_first_run:
                is_first_run = False
                logger.info("Initialization complete, will now monitor for changes")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
        
        # Sleep for remaining time to maintain interval
        elapsed = time.time() - cycle_start
        sleep_time = max(0, CHECK_INTERVAL - elapsed)
        
        if sleep_time > 0 and not shutdown_flag:
            logger.debug(f"Sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
    
    logger.info("Monitor stopped")


def check_github(
    monitor: GitHubMonitor,
    state_manager: StateManager,
    old_state: Dict[str, Any],
    is_first_run: bool
) -> Dict[str, Any]:
    """Check GitHub for changes."""
    try:
        new_state = monitor.fetch_current_state()
        
        if new_state is None:
            logger.warning("Failed to fetch GitHub state, skipping this cycle")
            return {}
        
        # Detect changes
        changes = monitor.detect_changes(old_state, new_state)
        
        # Update state file
        state_manager.save_state(GITHUB_STATE_FILE, new_state)
        
        # Update in-memory state for next cycle
        old_state.clear()
        old_state.update(new_state)
        
        repo_count = len(new_state.get("repos", {}))
        logger.info(f"GitHub check complete: {repo_count} repos monitored")
        
        return changes
        
    except Exception as e:
        logger.error(f"Error checking GitHub: {e}", exc_info=True)
        return {}


def check_huggingface(
    monitor: HuggingFaceMonitor,
    state_manager: StateManager,
    old_state: Dict[str, Any],
    is_first_run: bool
) -> Dict[str, Any]:
    """Check HuggingFace for changes."""
    try:
        new_state = monitor.fetch_current_state()
        
        if new_state is None:
            logger.warning("Failed to fetch HuggingFace state, skipping this cycle")
            return {}
        
        # Detect changes
        changes = monitor.detect_changes(old_state, new_state)
        
        # Update state file
        state_manager.save_state(HUGGINGFACE_STATE_FILE, new_state)
        
        # Update in-memory state for next cycle
        old_state.clear()
        old_state.update(new_state)
        
        model_count = len(new_state.get("models", {}))
        dataset_count = len(new_state.get("datasets", {}))
        logger.info(f"HuggingFace check complete: {model_count} models, {dataset_count} datasets monitored")
        
        return changes
        
    except Exception as e:
        logger.error(f"Error checking HuggingFace: {e}", exc_info=True)
        return {}


def merge_changes(github_changes: Dict[str, Any], huggingface_changes: Dict[str, Any]) -> Dict[str, Any]:
    """Merge GitHub and HuggingFace changes into single notification payload."""
    merged = {
        "github_new_repos": github_changes.get("new_repos", []),
        "github_updated_repos": github_changes.get("updated_repos", []),
        "huggingface_new_models": huggingface_changes.get("new_models", []),
        "huggingface_updated_models": huggingface_changes.get("updated_models", []),
        "huggingface_new_datasets": huggingface_changes.get("new_datasets", []),
        "huggingface_updated_datasets": huggingface_changes.get("updated_datasets", [])
    }
    return merged


def has_changes(changes: Dict[str, Any]) -> bool:
    """Check if there are any actual changes to notify about."""
    return any(changes.values())


if __name__ == "__main__":
    main()
```

**Step 3: Commit**

```bash
git add main.py config.py
git commit -m "feat: add main application with monitoring loop"
```

---

## Task 7: Docker Setup

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "main.py"]
```

**Step 2: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  monitor:
    build: .
    container_name: deepseek-repo-monitor
    volumes:
      - ./state:/app/state
    environment:
      - WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e55bfcc3-4b1e-4656-8e70-7415d00f17f4
      - CHECK_INTERVAL=60
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Step 3: Create .dockerignore**

```
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# State files (will be mounted as volume)
state/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Documentation
docs/
README.md

# Testing
tests/
*.log
```

**Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: add Docker configuration for containerized deployment"
```

---

## Task 8: Update WeChat Notifier for Datasets

**Files:**
- Modify: `utils/wechat_notifier.py`

**Step 1: Add dataset sections to _format_message**

Find the `_format_message` method and add these sections after the HuggingFace model sections:

```python
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
```

**Step 2: Commit**

```bash
git add utils/wechat_notifier.py
git commit -m "feat: add dataset notifications to WeChat notifier"
```

---

## Task 9: Testing Script

**Files:**
- Create: `test_webhook.py`

**Step 1: Create test script**

```python
#!/usr/bin/env python3
"""
Test script for WeChat webhook notification.
Run this to verify webhook is working before starting the monitor.
"""
import sys
from utils.wechat_notifier import WeChatNotifier
from config import WECHAT_WEBHOOK_URL

def main():
    print(f"Testing WeChat webhook: {WECHAT_WEBHOOK_URL}")
    
    notifier = WeChatNotifier(WECHAT_WEBHOOK_URL)
    
    # Test notification with sample data
    test_changes = {
        "github_new_repos": [
            {
                "name": "test-repo",
                "url": "https://github.com/deepseek-ai/test-repo"
            }
        ],
        "github_updated_repos": [
            {
                "name": "existing-repo",
                "url": "https://github.com/deepseek-ai/existing-repo",
                "commit_count": 3
            }
        ],
        "huggingface_new_models": [
            {
                "name": "deepseek-ai/test-model",
                "url": "https://huggingface.co/deepseek-ai/test-model"
            }
        ],
        "huggingface_updated_models": [],
        "huggingface_new_datasets": [],
        "huggingface_updated_datasets": []
    }
    
    success = notifier.send_notification(test_changes)
    
    if success:
        print("✓ Test notification sent successfully!")
        sys.exit(0)
    else:
        print("✗ Failed to send test notification")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

```bash
chmod +x test_webhook.py
```

**Step 3: Commit**

```bash
git add test_webhook.py
git commit -m "feat: add webhook testing script"
```

---

## Task 10: Final Documentation Update

**Files:**
- Modify: `README.md`

**Step 1: Update README with detailed usage**

Replace the README.md content with:

```markdown
# DeepSeek Repository Monitor

Monitors DeepSeek's GitHub and HuggingFace repositories for changes and sends notifications via WeChat Work.

## Features

- 🔍 Monitors GitHub organization: https://github.com/deepseek-ai
- 🤗 Monitors HuggingFace organization: https://huggingface.co/deepseek-ai
- 📦 Detects new repositories, models, and datasets
- 📝 Detects new commits in existing repositories
- 📱 Sends notifications via WeChat Work webhook
- ⏱️ Runs continuously with 60-second check intervals
- 💾 State persisted in JSON files
- 🐳 Containerized with Docker

## Architecture

```
deepseek-repo-monitor/
├── main.py                 # Main application loop
├── config.py              # Configuration settings
├── monitors/
│   ├── github_monitor.py      # GitHub API integration
│   └── huggingface_monitor.py # HuggingFace API integration
├── utils/
│   ├── state_manager.py       # JSON state persistence
│   └── wechat_notifier.py     # WeChat Work notifications
├── state/                     # State files (created at runtime)
│   ├── github_state.json
│   └── huggingface_state.json
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup

### Prerequisites

- Docker and docker-compose installed
- WeChat Work webhook URL (configure in `docker-compose.yml`)

### Quick Start

1. **Clone and enter directory:**
   ```bash
   cd deepseek-repo-monitor
   ```

2. **Configure webhook URL** (optional if using default):
   Edit `docker-compose.yml` and update `WECHAT_WEBHOOK_URL`

3. **Test webhook** (optional but recommended):
   ```bash
   python test_webhook.py
   ```

4. **Build and run:**
   ```bash
   docker-compose up -d
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f monitor
   ```

6. **Stop service:**
   ```bash
   docker-compose down
   ```

## Configuration

Environment variables (set in `docker-compose.yml`):

- `WECHAT_WEBHOOK_URL` - WeChat Work webhook endpoint (required)
- `CHECK_INTERVAL` - Seconds between checks (default: 60)

## State Files

State is stored in `./state/` directory:

- `github_state.json` - GitHub repos and last commit SHAs
- `huggingface_state.json` - HuggingFace models/datasets and timestamps

**Note:** On first run, the monitor initializes state silently without sending notifications.

## Notification Format

Notifications are sent in markdown format with sections:

- 🆕 New GitHub Repositories
- 📝 GitHub Repository Updates (with commit counts)
- 🤗 New HuggingFace Models
- 🔄 HuggingFace Model Updates
- 🗂️ New HuggingFace Datasets
- 🔄 HuggingFace Dataset Updates

## Logging

Logs include:
- Service startup and configuration
- Check cycle heartbeats
- Changes detected
- Notifications sent
- API errors and rate limits
- Network issues

View logs: `docker-compose logs -f monitor`

## Development

### Running without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py
```

### Testing

Test webhook connectivity:
```bash
python test_webhook.py
```

## API Rate Limits

- **GitHub**: 60 requests/hour (unauthenticated)
- **HuggingFace**: Generous limits for public APIs

The monitor handles rate limits gracefully and continues monitoring.

## Troubleshooting

**No notifications received:**
1. Check webhook URL is correct
2. Run `python test_webhook.py` to verify connectivity
3. Check logs for errors: `docker-compose logs monitor`

**State not persisting:**
- Ensure `./state/` directory has proper permissions
- Check Docker volume mount in `docker-compose.yml`

**API errors:**
- Check network connectivity
- Verify GitHub/HuggingFace are accessible
- Review rate limit messages in logs

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: comprehensive README with usage and troubleshooting"
```

---

## Plan Complete

All components have been implemented:
- ✅ State management with JSON persistence
- ✅ WeChat Work notifications with markdown formatting
- ✅ GitHub monitoring (repos and commits)
- ✅ HuggingFace monitoring (models and datasets)
- ✅ Main application with continuous monitoring loop
- ✅ Docker containerization
- ✅ Testing utilities
- ✅ Comprehensive documentation

**Next Steps:**
1. Build the Docker image: `docker-compose build`
2. Test webhook: `python test_webhook.py`
3. Start monitoring: `docker-compose up -d`
4. Monitor logs: `docker-compose logs -f monitor`
