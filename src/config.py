"""
Configuration loader for KAVAK Market Research
"""
import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Look for settings.yaml, fall back to settings.example.yaml
            base_path = Path(__file__).parent.parent / "config"
            config_path = base_path / "settings.yaml"
            if not config_path.exists():
                config_path = base_path / "settings.example.yaml"

        self._config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load YAML configuration file"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        config = self._substitute_env_vars(config)
        return config

    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute ${VAR} with environment variables"""
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                return os.environ.get(var_name, obj)
            return obj
        elif isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    @property
    def cities(self) -> list:
        """Get all configured cities (tier 1 + tier 2)"""
        tier1 = self.get("geography.tier1_cities", [])
        tier2 = self.get("geography.tier2_cities", [])
        return tier1 + tier2

    @property
    def tier1_cities(self) -> list:
        """Get tier 1 cities only"""
        return self.get("geography.tier1_cities", [])

    @property
    def price_buckets(self) -> list:
        """Get price bucket definitions"""
        return self.get("price_buckets", [])

    @property
    def brand_tiers(self) -> dict:
        """Get brand tier mappings"""
        return self.get("brand_tiers", {})

    @property
    def output_path(self) -> Path:
        """Get output directory path"""
        return Path(self.get("output.path", "./data/outputs/"))

    @property
    def raw_data_path(self) -> Path:
        """Get raw data directory path"""
        return Path(__file__).parent.parent / "data" / "raw"

    @property
    def processed_data_path(self) -> Path:
        """Get processed data directory path"""
        return Path(__file__).parent.parent / "data" / "processed"

    # INEGI configuration
    @property
    def inegi_api_url(self) -> str:
        return self.get("sources.inegi.api_url", "")

    @property
    def inegi_api_token(self) -> str:
        return self.get("sources.inegi.api_token", "")

    # Autocosmos configuration
    @property
    def autocosmos_base_url(self) -> str:
        return self.get("sources.new_car_pricing.autocosmos.base_url",
                        "https://www.autocosmos.com.mx")

    # KAVAK API configuration
    @property
    def kavak_api_url(self) -> str:
        return self.get("sources.kavak.api.base_url", "")

    @property
    def kavak_api_key(self) -> str:
        return self.get("sources.kavak.api.api_key", "")


# Global config instance
_config = None


def get_config() -> Config:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
