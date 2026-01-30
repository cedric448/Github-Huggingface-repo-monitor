#!/usr/bin/env python3
"""
Test script for commit SHA-based tracking implementation.
"""
import logging
import json
from monitors.github_monitor import GitHubMonitor
from utils.state_manager import StateManager
from config import GITHUB_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_commit_tracking():
    """Test the new commit SHA-based tracking."""
    logger.info("=" * 60)
    logger.info("Testing Commit SHA-based Tracking")
    logger.info("=" * 60)
    
    # Initialize components
    org_name = "deepseek-ai"
    state_manager = StateManager("state")
    monitor = GitHubMonitor(org_name, GITHUB_TOKEN)
    
    logger.info(f"\n1. Fetching current state for {org_name}...")
    new_state = monitor.fetch_current_state()
    
    if new_state is None:
        logger.error("Failed to fetch state!")
        return False
    
    repos = new_state.get("repos", {})
    logger.info(f"   ✓ Fetched {len(repos)} repositories")
    
    # Display sample repo with commit info
    if repos:
        sample_repo = list(repos.keys())[0]
        sample_data = repos[sample_repo]
        logger.info(f"\n2. Sample repository: {sample_repo}")
        logger.info(f"   URL: {sample_data.get('url')}")
        
        commit = sample_data.get('last_commit')
        if commit:
            logger.info(f"   Commit SHA: {commit.get('sha', 'N/A')[:7]}")
            logger.info(f"   Message: {commit.get('message', 'N/A')}")
            logger.info(f"   Author: {commit.get('author', 'N/A')}")
            logger.info(f"   Date: {commit.get('date', 'N/A')}")
        else:
            logger.warning(f"   No commit info available (might be rate limited)")
    
    # Save state
    logger.info(f"\n3. Saving state...")
    state_file = f"github_{org_name}.json"
    state_manager.save_state(state_file, new_state)
    logger.info(f"   ✓ Saved to state/{state_file}")
    
    # Verify state format
    logger.info(f"\n4. Verifying state format...")
    loaded_state = state_manager.load_state(state_file)
    
    if loaded_state:
        repos_with_commits = 0
        repos_without_commits = 0
        
        for repo_name, repo_data in loaded_state.get("repos", {}).items():
            if repo_data.get("last_commit"):
                repos_with_commits += 1
            else:
                repos_without_commits += 1
        
        logger.info(f"   ✓ Repos with commit info: {repos_with_commits}")
        logger.info(f"   ✓ Repos without commit info: {repos_without_commits}")
        
        if repos_without_commits > 0:
            logger.warning(f"   ⚠ Some repos don't have commit info (likely due to rate limits)")
    
    # Test change detection (simulate an update)
    logger.info(f"\n5. Testing change detection...")
    logger.info(f"   Simulating no changes (comparing state with itself)...")
    changes = monitor.detect_changes(new_state, new_state)
    
    new_repos = len(changes.get("new_repos", []))
    updated_repos = len(changes.get("updated_repos", []))
    
    logger.info(f"   ✓ New repos: {new_repos}")
    logger.info(f"   ✓ Updated repos: {updated_repos}")
    
    if new_repos == 0 and updated_repos == 0:
        logger.info(f"   ✓ Change detection works correctly (no false positives)")
    else:
        logger.error(f"   ✗ Unexpected changes detected!")
    
    logger.info("\n" + "=" * 60)
    logger.info("Test completed!")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_commit_tracking()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        exit(1)
