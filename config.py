import os
import yaml
from pathlib import Path

# Load configuration from YAML file
CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.yaml")

def load_config():
    """Load configuration from YAML file with fallback to defaults."""
    config_path = Path(CONFIG_FILE)
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}\n"
            "Please create config.yaml or set CONFIG_FILE environment variable."
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

# Load configuration
_config = load_config()

# GitHub configuration
GITHUB_TOKEN = _config.get('github_token')
GITHUB_ORGS = _config.get('github_orgs', ['deepseek-ai'])

# HuggingFace configuration
HUGGINGFACE_ORGS = _config.get('huggingface_orgs', ['deepseek-ai'])

# WeChat configuration
WECHAT_WEBHOOK_URL = _config.get('wechat_webhook_url')
if not WECHAT_WEBHOOK_URL:
    raise ValueError("wechat_webhook_url must be set in config.yaml")

# Check interval
CHECK_INTERVAL = _config.get('check_interval', 60)

# State storage
STATE_DIR = _config.get('state_dir', 'state')
GITHUB_STATE_FILE = "github_state.json"
HUGGINGFACE_STATE_FILE = "huggingface_state.json"
