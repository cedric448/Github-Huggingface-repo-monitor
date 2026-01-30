#!/usr/bin/env python3
"""
Test script to demonstrate commit change detection.
"""
import logging
import json
from monitors.github_monitor import GitHubMonitor
from utils.wechat_notifier import WeChatNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_change_detection():
    """Test change detection with simulated commit updates."""
    logger.info("=" * 60)
    logger.info("Testing Change Detection with Commit SHA")
    logger.info("=" * 60)
    
    # Load the current state
    with open('state/github_deepseek-ai.json', 'r') as f:
        current_state = json.load(f)
    
    logger.info(f"\nLoaded state with {len(current_state['repos'])} repos")
    
    # Simulate an old state (change one commit)
    old_state = json.loads(json.dumps(current_state))  # Deep copy
    
    # Pick a repo to simulate a commit change
    test_repo = "DeepSeek-Coder"
    if test_repo in old_state['repos']:
        old_commit = old_state['repos'][test_repo]['last_commit']
        logger.info(f"\n1. Original commit for {test_repo}:")
        logger.info(f"   SHA: {old_commit['sha'][:7]}")
        logger.info(f"   Message: {old_commit['message']}")
        logger.info(f"   Author: {old_commit['author']}")
        
        # Simulate a new commit
        old_state['repos'][test_repo]['last_commit']['sha'] = 'abc1234567890' + old_commit['sha'][13:]
        old_state['repos'][test_repo]['last_commit']['message'] = 'feat: add new feature X'
        old_state['repos'][test_repo]['last_commit']['author'] = 'Test Developer'
        
        logger.info(f"\n2. Simulated OLD state (before update):")
        logger.info(f"   SHA: {old_state['repos'][test_repo]['last_commit']['sha'][:7]}")
        logger.info(f"   Message: {old_state['repos'][test_repo]['last_commit']['message']}")
        logger.info(f"   Author: {old_state['repos'][test_repo]['last_commit']['author']}")
        
        logger.info(f"\n3. Current state (NEW commit):")
        logger.info(f"   SHA: {current_state['repos'][test_repo]['last_commit']['sha'][:7]}")
        logger.info(f"   Message: {current_state['repos'][test_repo]['last_commit']['message']}")
        logger.info(f"   Author: {current_state['repos'][test_repo]['last_commit']['author']}")
    
    # Test change detection
    logger.info(f"\n4. Running change detection...")
    monitor = GitHubMonitor("deepseek-ai")
    changes = monitor.detect_changes(old_state, current_state)
    
    logger.info(f"\n5. Detection Results:")
    logger.info(f"   New repos: {len(changes.get('new_repos', []))}")
    logger.info(f"   Updated repos: {len(changes.get('updated_repos', []))}")
    
    if changes.get('updated_repos'):
        logger.info(f"\n6. Updated Repository Details:")
        for repo in changes['updated_repos']:
            logger.info(f"   Repository: {repo['name']}")
            logger.info(f"   URL: {repo['url']}")
            commit = repo.get('commit', {})
            logger.info(f"   Commit SHA: {commit.get('sha', 'N/A')}")
            logger.info(f"   Message: {commit.get('message', 'N/A')}")
            logger.info(f"   Author: {commit.get('author', 'N/A')}")
    
    # Test notification formatting
    logger.info(f"\n7. Testing Notification Format:")
    logger.info("-" * 60)
    
    notifier = WeChatNotifier("dummy_webhook_url")
    message = notifier._format_message({
        "github_new_repos": [],
        "github_updated_repos": changes.get('updated_repos', []),
        "huggingface_new_models": [],
        "huggingface_updated_models": [],
        "huggingface_new_datasets": [],
        "huggingface_updated_datasets": []
    })
    
    print(message)
    logger.info("-" * 60)
    
    logger.info("\n" + "=" * 60)
    logger.info("Change Detection Test Completed!")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_change_detection()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        exit(1)
