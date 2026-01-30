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
