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
                logger.info(f"Fetched {len(state['models'])} models from HuggingFace ({self.org_name})")
            
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
                logger.info(f"Fetched {len(state['datasets'])} datasets from HuggingFace ({self.org_name})")
            
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
                logger.info(f"New model detected: {model_id} ({self.org_name})")
        
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
                    logger.info(f"Model updated: {model_id} ({self.org_name})")
        
        # Detect new datasets
        for dataset_id, dataset_data in new_datasets.items():
            if dataset_id not in old_datasets:
                changes["new_datasets"].append({
                    "name": dataset_id,
                    "url": dataset_data["url"]
                })
                logger.info(f"New dataset detected: {dataset_id} ({self.org_name})")
        
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
                    logger.info(f"Dataset updated: {dataset_id} ({self.org_name})")
        
        return changes
