# GitHub & HuggingFace Repository Monitor

Monitors GitHub and HuggingFace repositories for changes and sends notifications via WeChat Work.

## ✨ Features

- 🔍 **Multi-Organization Monitoring**: Track multiple GitHub/HuggingFace orgs simultaneously
- 🎯 **Commit SHA Tracking**: Precise change detection based on commit SHA (not timestamps)
- 📝 **Rich Commit Details**: Shows commit message, author, and SHA in notifications
- 📦 **New Repository Detection**: Get notified when new repos are created
- 📱 **WeChat Work Integration**: Beautiful markdown-formatted notifications
- ⏱️ **Configurable Intervals**: Set your preferred check frequency (default: 60s)
- 💾 **State Persistence**: JSON-based state management
- 🐳 **Docker Ready**: Easy deployment with Docker Compose
- 🔧 **YAML Configuration**: Simple, readable configuration file

## 🆕 What's New in v3.0

- ✅ **Commit SHA-based tracking** replaces pushed_at timestamps
- ✅ **Zero false positives** - only real commits trigger notifications
- ✅ **Full commit metadata** - see who changed what and why
- ✅ **Organization labels** - know which org each change belongs to
- ✅ **Better notification format** - more informative and readable

**Example Notification**:
```markdown
## 📝 GitHub Repository Updates
- [deepseek-ai] [DeepSeek-Coder](https://github.com/...)
  `2f9fd85` Merge pull request #673 from DillionApple/patch-1 *by ZHU QIHAO*
```

👉 **Upgrading from v2.x?** See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)  
👉 **Implementation details?** See [COMMIT_SHA_IMPLEMENTATION_REPORT.md](COMMIT_SHA_IMPLEMENTATION_REPORT.md)

## Architecture

```
deepseek-repo-monitor/
├── main.py                     # Main application loop
├── config.py                   # Configuration loader
├── config.yaml                 # Configuration file (YOU EDIT THIS)
├── monitors/
│   ├── github_monitor.py       # GitHub API integration
│   └── huggingface_monitor.py  # HuggingFace API integration
├── utils/
│   ├── state_manager.py        # JSON state persistence
│   └── wechat_notifier.py      # WeChat Work notifications
├── state/                      # State files (created at runtime)
│   ├── github_deepseek-ai.json
│   └── huggingface_deepseek-ai.json
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup

### Prerequisites

- Docker and docker-compose installed
- WeChat Work webhook URL
- (Optional) GitHub Personal Access Token for higher rate limits

### Quick Start

1. **Clone and enter directory:**
   ```bash
   cd deepseek-repo-monitor
   ```

2. **Edit `config.yaml` to configure your monitoring:**
   ```yaml
   # GitHub Access Token (optional but recommended)
   github_token: ghp_your_token_here
   
   # Check interval in seconds
   check_interval: 60
   
   # WeChat Work webhook URL
   wechat_webhook_url: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
   
   # GitHub organizations/users to monitor
   github_orgs:
     - deepseek-ai
     - openai
     # Add more here...
   
   # HuggingFace organizations/users to monitor
   huggingface_orgs:
     - deepseek-ai
     - meta-llama
     # Add more here...
   ```

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

### GitHub Token (Recommended)

To avoid rate limit issues and enable commit tracking, add a GitHub Personal Access Token in `config.yaml`:
- **Without token:** 60 requests/hour ❌ (not enough for commit tracking)
- **With token:** 5000 requests/hour ✅ (recommended for production)

**Why you need it**: The new commit SHA tracking makes ~32 API requests per check cycle. Without a token, you'll hit rate limits quickly.

See [GITHUB_TOKEN_SETUP.md](GITHUB_TOKEN_SETUP.md) for setup instructions.

## Configuration

All configuration is in `config.yaml`:

### Main Settings

- `github_token` - GitHub Personal Access Token (optional but recommended)
- `check_interval` - Seconds between checks (default: 60)
- `wechat_webhook_url` - WeChat Work webhook endpoint (required)
- `state_dir` - Directory for state files (default: "state")

### Adding More Organizations

Simply add more entries to the lists:

```yaml
github_orgs:
  - deepseek-ai      # Already configured
  - anthropics       # Add Anthropic
  - openai           # Add OpenAI
  - meta-llama       # Add Meta

huggingface_orgs:
  - deepseek-ai      # Already configured
  - mistralai        # Add Mistral
  - google           # Add Google
```

**Note:** Each organization will have its own state file, e.g.:
- `state/github_deepseek-ai.json`
- `state/github_openai.json`
- `state/huggingface_mistralai.json`

## State Files

State is stored in `./state/` directory:

- `github_<org-name>.json` - GitHub repos with commit SHA and metadata
- `huggingface_<org-name>.json` - HuggingFace models/datasets with timestamps

**State Format (v3.0)**:
```json
{
  "repos": {
    "DeepSeek-Coder": {
      "id": 707551301,
      "url": "https://github.com/deepseek-ai/DeepSeek-Coder",
      "default_branch": "main",
      "last_commit": {
        "sha": "2f9fd85927c669dae3c0fbb2d607274023af243e",
        "message": "Merge pull request #673",
        "author": "ZHU QIHAO",
        "date": "2025-11-11T06:44:55Z"
      }
    }
  }
}
```

**Note:** On first run, the monitor initializes state silently without sending notifications.

## Notification Format

Notifications are sent in markdown format with detailed information:

### GitHub Updates (New in v3.0)
```markdown
## 🆕 New GitHub Repositories
- [deepseek-ai] [repo-name](url)

## 📝 GitHub Repository Updates
- [deepseek-ai] [DeepSeek-Coder](url)
  `2f9fd85` Merge pull request #673 from DillionApple/patch-1 *by ZHU QIHAO*
```

### HuggingFace Updates
```markdown
## 🤗 New HuggingFace Models
- [org-name] [model-name](url)

## 🔄 HuggingFace Model Updates
- [org-name] [model-name](url)
```

**All changes from all monitored organizations are combined into a single notification.**

## Logging

Logs include:
- Service startup and configuration
- Which organizations are being monitored
- Check cycle heartbeats for each organization
- **Commit-level change detection** (SHA, author, message)
- Changes detected (with organization name)
- Notifications sent
- API errors and rate limits
- Network issues

**Example logs**:
```
[2026-01-25 21:35:00] INFO - Fetched 31 repositories from GitHub (deepseek-ai)
[2026-01-25 21:36:10] INFO - New commit detected in DeepSeek-Coder (deepseek-ai): 2f9fd85 by ZHU QIHAO
[2026-01-25 21:36:11] INFO - Notification sent successfully
```

View logs: `docker-compose logs -f monitor`

## Development

### Running without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Edit config.yaml with your settings

# Run directly
python main.py
```

### Testing

Test webhook connectivity:
```bash
python test_webhook.py
```

## API Rate Limits

- **GitHub**: 
  - Without token: 60 requests/hour (not enough for multiple orgs)
  - With token: 5000 requests/hour (recommended)
- **HuggingFace**: Generous limits for public APIs

The monitor handles rate limits gracefully and continues monitoring.

## Troubleshooting

**No notifications received:**
1. Check `config.yaml` has correct webhook URL
2. Run `python test_webhook.py` to verify connectivity
3. Check logs for errors: `docker-compose logs monitor`

**Config file not found:**
- Ensure `config.yaml` exists in the project root
- Check Docker volume mount in `docker-compose.yml`

**State not persisting:**
- Ensure `./state/` directory has proper permissions
- Check Docker volume mount in `docker-compose.yml`

**API errors:**
- Check network connectivity
- Verify GitHub/HuggingFace are accessible
- Review rate limit messages in logs
- Add GitHub token if hitting rate limits

## Example Use Cases

### Monitor Multiple AI Labs
```yaml
github_orgs:
  - deepseek-ai
  - openai
  - anthropics
  - meta-llama

huggingface_orgs:
  - deepseek-ai
  - openai
  - mistralai
  - google
```

### Monitor Specific Projects
```yaml
# GitHub supports both orgs and individual users
github_orgs:
  - deepseek-ai
  - torvalds        # Individual user
  - vercel          # Another org

huggingface_orgs:
  - deepseek-ai
  - stabilityai
```

## License

MIT
