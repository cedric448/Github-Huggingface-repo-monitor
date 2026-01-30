#!/usr/bin/env python3
import logging
import time
import signal
import sys
from typing import Dict, Any, List

from config import (
    WECHAT_WEBHOOK_URL,
    CHECK_INTERVAL,
    GITHUB_ORGS,
    HUGGINGFACE_ORGS,
    GITHUB_TOKEN,
    STATE_DIR
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
    logger.info(f"Monitoring GitHub orgs: {', '.join(GITHUB_ORGS)}")
    logger.info(f"Monitoring HuggingFace orgs: {', '.join(HUGGINGFACE_ORGS)}")
    
    # Initialize components
    state_manager = StateManager(STATE_DIR)
    notifier = WeChatNotifier(WECHAT_WEBHOOK_URL)
    
    # Create monitors for each organization
    github_monitors = {
        org: GitHubMonitor(org, GITHUB_TOKEN)
        for org in GITHUB_ORGS
    }
    
    huggingface_monitors = {
        org: HuggingFaceMonitor(org)
        for org in HUGGINGFACE_ORGS
    }
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load existing state for each organization
    github_states = {
        org: state_manager.load_state(f"github_{org.replace('/', '_')}.json")
        for org in GITHUB_ORGS
    }
    
    huggingface_states = {
        org: state_manager.load_state(f"huggingface_{org.replace('/', '_')}.json")
        for org in HUGGINGFACE_ORGS
    }
    
    # Check if this is first run (no state for any org)
    is_first_run = all(state is None for state in github_states.values()) and \
                   all(state is None for state in huggingface_states.values())
    
    if is_first_run:
        logger.info("First run detected, will initialize state silently")
    
    logger.info("Starting monitoring loop...")
    
    while not shutdown_flag:
        cycle_start = time.time()
        
        try:
            all_changes = []
            
            # Check all GitHub organizations
            for org in GITHUB_ORGS:
                github_changes = check_github(
                    github_monitors[org],
                    state_manager,
                    github_states[org],
                    org,
                    is_first_run
                )
                if github_changes:
                    all_changes.append(github_changes)
            
            # Check all HuggingFace organizations
            for org in HUGGINGFACE_ORGS:
                huggingface_changes = check_huggingface(
                    huggingface_monitors[org],
                    state_manager,
                    huggingface_states[org],
                    org,
                    is_first_run
                )
                if huggingface_changes:
                    all_changes.append(huggingface_changes)
            
            # Send notification if there are changes and not first run
            if not is_first_run and all_changes:
                merged_changes = merge_all_changes(all_changes)
                if has_changes(merged_changes):
                    notifier.send_notification(merged_changes)
            
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
    org_name: str,
    is_first_run: bool
) -> Dict[str, Any]:
    """Check GitHub for changes."""
    try:
        new_state = monitor.fetch_current_state()
        
        if new_state is None:
            logger.warning(f"Failed to fetch GitHub state for {org_name}, skipping this cycle")
            return {}
        
        # Detect changes
        changes = monitor.detect_changes(old_state, new_state)
        
        # Update state file
        state_file = f"github_{org_name.replace('/', '_')}.json"
        state_manager.save_state(state_file, new_state)
        
        # Update in-memory state for next cycle
        if old_state is not None:
            old_state.clear()
            old_state.update(new_state)
        else:
            # Update the dictionary in the parent scope
            github_states[org_name] = new_state
        
        repo_count = len(new_state.get("repos", {}))
        logger.info(f"GitHub check complete ({org_name}): {repo_count} repos monitored")
        
        return changes
        
    except Exception as e:
        logger.error(f"Error checking GitHub {org_name}: {e}", exc_info=True)
        return {}


def check_huggingface(
    monitor: HuggingFaceMonitor,
    state_manager: StateManager,
    old_state: Dict[str, Any],
    org_name: str,
    is_first_run: bool
) -> Dict[str, Any]:
    """Check HuggingFace for changes."""
    try:
        new_state = monitor.fetch_current_state()
        
        if new_state is None:
            logger.warning(f"Failed to fetch HuggingFace state for {org_name}, skipping this cycle")
            return {}
        
        # Detect changes
        changes = monitor.detect_changes(old_state, new_state)
        
        # Update state file
        state_file = f"huggingface_{org_name.replace('/', '_')}.json"
        state_manager.save_state(state_file, new_state)
        
        # Update in-memory state for next cycle
        if old_state is not None:
            old_state.clear()
            old_state.update(new_state)
        else:
            # Update the dictionary in the parent scope
            huggingface_states[org_name] = new_state
        
        model_count = len(new_state.get("models", {}))
        dataset_count = len(new_state.get("datasets", {}))
        logger.info(f"HuggingFace check complete ({org_name}): {model_count} models, {dataset_count} datasets monitored")
        
        return changes
        
    except Exception as e:
        logger.error(f"Error checking HuggingFace {org_name}: {e}", exc_info=True)
        return {}


def merge_all_changes(changes_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge all changes from multiple organizations into single notification payload."""
    merged = {
        "github_new_repos": [],
        "github_updated_repos": [],
        "huggingface_new_models": [],
        "huggingface_updated_models": [],
        "huggingface_new_datasets": [],
        "huggingface_updated_datasets": []
    }
    
    for changes in changes_list:
        merged["github_new_repos"].extend(changes.get("new_repos", []))
        merged["github_updated_repos"].extend(changes.get("updated_repos", []))
        merged["huggingface_new_models"].extend(changes.get("new_models", []))
        merged["huggingface_updated_models"].extend(changes.get("updated_models", []))
        merged["huggingface_new_datasets"].extend(changes.get("new_datasets", []))
        merged["huggingface_updated_datasets"].extend(changes.get("updated_datasets", []))
    
    return merged


def has_changes(changes: Dict[str, Any]) -> bool:
    """Check if there are any actual changes to notify about."""
    return any(changes.values())


# Make states accessible to check functions
github_states = {}
huggingface_states = {}


if __name__ == "__main__":
    main()
