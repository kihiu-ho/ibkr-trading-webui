"""Configuration loader for trading workflows."""
import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Load and manage workflow configuration from YAML files."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to configuration YAML file.
                        Defaults to /opt/airflow/config/trading_workflow.yaml
        """
        if config_path is None:
            config_path = os.getenv(
                'TRADING_WORKFLOW_CONFIG',
                '/opt/airflow/config/trading_workflow.yaml'
            )
        
        self.config_path = Path(config_path)
        self._config = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get configuration, loading if necessary."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def get_backend_config(self) -> Dict[str, Any]:
        """Get backend API configuration."""
        return self.config.get('backend', {})
    
    def get_mlflow_config(self) -> Dict[str, Any]:
        """Get MLflow configuration."""
        return self.config.get('mlflow', {})
    
    def get_market_config(self) -> Dict[str, Any]:
        """Get market configuration."""
        return self.config.get('market', {})
    
    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get configuration for a specific workflow."""
        workflows = self.config.get('workflows', {})
        if workflow_name not in workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found in configuration")
        return workflows[workflow_name]
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default workflow settings."""
        return self.config.get('defaults', {})
    
    def reload(self):
        """Reload configuration from file."""
        self._config = None


# Global configuration instance
config_loader = ConfigLoader()

