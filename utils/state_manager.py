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
