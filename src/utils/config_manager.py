import json
import os
from pathlib import Path
from datetime import datetime

class ConfigManager:
    """Manages application configuration and preferences"""
    
    def __init__(self, config_file="config.json"):
        # Determine config file path
        if os.path.dirname(config_file) == "":
            # Use user's home directory for config file
            self.config_dir = Path.home() / ".pdf_merger"
            self.config_dir.mkdir(exist_ok=True)
            self.config_path = self.config_dir / config_file
        else:
            self.config_path = Path(config_file)
        
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "theme": "system",
            "last_directory": str(Path.home()),
            "window_width": 900,
            "window_height": 600,
            "window_x": None,
            "window_y": None,
            "version": "1.0.0",
            "sort_method": "alphabetical",
            "show_file_details": True
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults (in case new settings were added)
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                
                return loaded_config
            else:
                return default_config.copy()
                
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config.copy()
    
    def save(self):
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
    
    def delete(self, key):
        """Delete a configuration key"""
        if key in self.config:
            del self.config[key]