# DeepSeek Repository Monitor - Design Document

**Date:** 2026-01-24

## Requirements

Monitor DeepSeek's GitHub and HuggingFace repositories for changes and send notifications via WeChat Work webhook.

**Monitored Resources:**
- GitHub organization: https://github.com/deepseek-ai
- HuggingFace organization: https://huggingface.co/deepseek-ai

**Notification webhook:**
- WeChat Work: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e55bfcc3-4b1e-4656-8e70-7415d00f17f4

**Monitoring scope:**
- Repository-level: New repos, deleted repos
- Commit-level: New commits to existing repos

**Monitoring frequency:** Every 60 seconds

**Initial state handling:** Record existing state silently without notifications

---

## Architecture Overview

The monitoring service is a Python application running in a Docker container with these core components:

**Main Loop**: A continuous process that runs every 60 seconds, checking both GitHub and HuggingFace for changes.

**State Manager**: Handles reading/writing JSON state files that track what's been seen. Two state files:
- `state/github_state.json` - Stores repo list and latest commit SHAs per repo
- `state/huggingface_state.json` - Stores model/dataset list and their last update times

**API Clients**: Separate modules for GitHub and HuggingFace APIs using the `requests` library. Both use public unauthenticated endpoints.

**Notifier**: Sends markdown-formatted messages to WeChat Work webhook with repo names, change types, counts, and direct links.

**Error Handling**: Graceful handling of API failures, rate limits, and network issues with logging. Service continues running even if one check fails.

The Docker setup will use a volume mount for the `state/` directory so data persists across container restarts.

---

## Component Details

**GitHub Monitor** (`monitors/github_monitor.py`):
- Fetches all repos from `https://api.github.com/orgs/deepseek-ai/repos`
- For each repo, gets the default branch's latest commit via `/repos/{owner}/{repo}/commits`
- Detects new repos by comparing against stored repo list
- Detects new commits by comparing commit SHAs against stored state
- Returns structured change data (new repos list, repos with new commits and count)

**HuggingFace Monitor** (`monitors/huggingface_monitor.py`):
- Queries HuggingFace API: `https://huggingface.co/api/models?author=deepseek-ai`
- Also checks datasets: `https://huggingface.co/api/datasets?author=deepseek-ai`
- Tracks last modified timestamps for each model/dataset
- Detects additions and updates by comparing timestamps
- Returns structured change data (new models/datasets, updated items)

**State Manager** (`utils/state_manager.py`):
- Simple class with `load_state(filepath)` and `save_state(filepath, data)` methods
- Creates state directory if missing
- Handles JSON serialization/deserialization
- On first run, saves current state without triggering notifications

**WeChat Notifier** (`utils/wechat_notifier.py`):
- Formats messages in markdown with sections for each change type
- Example: "🆕 New Repository: [repo-name](link)" or "📝 Updates in [repo-name](link): 3 new commits"
- Sends POST request to webhook with proper JSON structure for WeChat Work
- Handles API errors gracefully

---

## Data Flow

**Startup Sequence**:
1. Application initializes, loads configuration (webhook URL, check interval)
2. State Manager checks if state files exist
3. If no state files (first run): Fetch current repos/commits, save silently, set `initialized=true` flag
4. If state files exist: Load previous state into memory

**Monitoring Cycle** (every 60 seconds):
1. GitHub Monitor fetches current org state from API
2. Compares against loaded state to detect changes
3. If changes found AND not first run: Collect change details
4. HuggingFace Monitor does the same for models/datasets
5. If any changes detected: Format and send notification via WeChat Notifier
6. Update state files with new current state
7. Sleep for remaining time to complete 60-second interval
8. Repeat

**Change Detection Logic**:
- New repos: Repos in current fetch not in previous state
- New commits: Compare latest commit SHA per repo; if different, count commits between old and new SHA
- New/updated models: Compare model IDs and lastModified timestamps
- All changes batched into single notification per cycle

**State File Structure**:
```json
{
  "initialized": true,
  "last_check": "2026-01-24T22:55:00Z",
  "repos": {
    "repo-name": {
      "id": 12345,
      "default_branch": "main",
      "last_commit_sha": "abc123..."
    }
  }
}
```

---

## Error Handling and Logging

**Logging Strategy**:
- Use Python's `logging` module with INFO level for normal operations, ERROR for failures
- Log format: `[%(asctime)s] %(levelname)s - %(message)s`
- Logs written to stdout (Docker will capture these)
- Key log events: Service start, each check cycle, changes detected, notifications sent, errors

**API Error Handling**:
- Wrap all API calls in try-except blocks
- Handle `requests.exceptions.RequestException` for network failures
- Check HTTP status codes: 200 OK, 403/429 for rate limits, 404 for missing resources
- On rate limit: Log warning, skip this cycle, continue monitoring
- On network failure: Log error, retry next cycle (don't crash service)
- On 404: Remove deleted repos from state, log the removal

**State File Error Handling**:
- If state file corrupted/invalid JSON: Log error, treat as first run (re-initialize)
- If can't write state: Log critical error but continue monitoring
- Ensure state directory exists before writing

**Notification Error Handling**:
- If webhook POST fails: Log error with status code and response
- Don't retry immediately (avoid notification spam)
- Service continues monitoring even if notification fails

**Graceful Shutdown**:
- Catch SIGTERM/SIGINT signals for Docker stop
- Save current state before exiting
- Log shutdown event

**Monitoring Health**:
- Log heartbeat message every cycle: "Check completed: X repos, Y commits checked"
- Helps verify service is running when no changes detected

---

## Testing Strategy

**Manual Testing Approach**:
- Test individual components with sample data before integration
- Create a `test_webhook.py` script to verify WeChat notification format
- Use a temporary state directory for testing to avoid polluting real state
- Test scenarios to verify manually:
  - First run initialization (should NOT send notifications)
  - New repo detection (create test state with fewer repos)
  - Commit detection (modify commit SHA in state file)
  - API error handling (test with invalid URLs)
  - State persistence across runs

---

## Docker Setup

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  monitor:
    build: .
    volumes:
      - ./state:/app/state
    environment:
      - WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e55bfcc3-4b1e-4656-8e70-7415d00f17f4
      - CHECK_INTERVAL=60
    restart: unless-stopped
```

**Dependencies** (`requirements.txt`):
```
requests==2.31.0
```

**Running the Service**:
- `docker-compose up -d` - Start in background
- `docker-compose logs -f monitor` - View logs
- `docker-compose down` - Stop service
- State persists in `./state/` directory on host
