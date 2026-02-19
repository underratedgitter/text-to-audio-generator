"""
Core Utilities Module
Provides shared functionality for logging, configuration, and common operations.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, Tuple, List
from dotenv import load_dotenv

# Project root (repo root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables
_dotenv_path = PROJECT_ROOT / ".env"
if _dotenv_path.exists():
    load_dotenv(dotenv_path=_dotenv_path)
else:
    load_dotenv()


class Config:
    """Configuration manager - loads and provides access to config.yaml"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = resolve_project_path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('video.target_length_seconds')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_env(self, env_var: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable"""
        return os.getenv(env_var, default)


class Logger:
    """Centralized logging utility"""
    
    @staticmethod
    def setup(name: str, config: Config) -> logging.Logger:
        """Setup logger with file and console handlers"""
        logger = logging.getLogger(name)
        
        # Prevent duplicate handlers
        if logger.hasHandlers():
            return logger
        
        # Get logging configuration
        log_level = config.get('logging.level', 'INFO')
        log_file = config.get('logging.log_file', 'logs/pipeline.log')
        
        # Create logs directory if it doesn't exist
        log_path = resolve_project_path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set logging level
        logger.setLevel(getattr(logging, log_level))
        
        # Console handler with color support
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # File handler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger


class FileManager:
    """Handles file operations and output directory management"""
    
    def __init__(self, config: Config):
        self.config = config
        base_dir = config.get('output.base_directory', 'output')
        self.base_output_dir = resolve_project_path(base_dir)
        
    def create_video_directory(self, video_id: Optional[str] = None) -> Path:
        """
        Create a unique directory for video assets
        Returns: Path to the created directory
        """
        if video_id is None:
            video_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        video_dir = self.base_output_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (video_dir / 'intermediates').mkdir(exist_ok=True)
        
        return video_dir
    
    def save_json(self, data: Dict[Any, Any], filepath: Path):
        """Save dictionary as JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_json(self, filepath: Path) -> Dict[Any, Any]:
        """Load JSON file as dictionary"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_asset_path(self, asset_type: str) -> Path:
        """Get path to asset directory (music, templates, etc.)"""
        asset_dir = PROJECT_ROOT / 'assets' / asset_type
        asset_dir.mkdir(parents=True, exist_ok=True)
        return asset_dir

    def get_timestamp(self) -> str:
        """Get formatted timestamp for file naming"""
        return get_timestamp()


class SafetyChecker:
    """Ensures content compliance and originality"""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.blacklist = config.get('safety.blacklist_keywords', [])
    
    def check_script_safety(self, script: str) -> Tuple[bool, List[str]]:
        """
        Check if script contains blacklisted keywords
        Returns: (is_safe, list of found violations)
        """
        violations = []
        script_lower = script.lower()
        
        for keyword in self.blacklist:
            if keyword.lower() in script_lower:
                violations.append(keyword)
        
        is_safe = len(violations) == 0
        
        if not is_safe:
            self.logger.warning(f"Script safety check failed. Violations: {violations}")
        
        return is_safe, violations
    
    def check_duplicate_content(self, new_script: str, video_dir: Path) -> float:
        """
        Compare new script against previously generated scripts
        Returns: Originality score (0.0 to 1.0, higher is more original)
        """
        # Get all previous scripts
        previous_scripts = []
        
        if self.config.get('output.archive_directory'):
            archive_dir = Path(self.config.get('output.archive_directory'))
            if archive_dir.exists():
                for script_file in archive_dir.rglob('script.json'):
                    try:
                        with open(script_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'full_script' in data:
                                previous_scripts.append(data['full_script'])
                    except Exception as e:
                        self.logger.warning(f"Error reading {script_file}: {e}")
        
        if not previous_scripts:
            return 1.0  # No previous scripts, assume original
        
        # Simple similarity check (word overlap ratio)
        new_words = set(new_script.lower().split())
        similarities = []
        
        for old_script in previous_scripts:
            old_words = set(old_script.lower().split())
            
            if not new_words or not old_words:
                continue
            
            overlap = len(new_words.intersection(old_words))
            similarity = overlap / max(len(new_words), len(old_words))
            similarities.append(similarity)
        
        if not similarities:
            return 1.0
        
        # Originality is inverse of max similarity
        max_similarity = max(similarities)
        originality = 1.0 - max_similarity
        
        self.logger.info(f"Originality score: {originality:.2f}")
        
        return originality


class ProgressTracker:
    """Track pipeline execution progress"""
    
    def __init__(self, video_dir: Path):
        self.video_dir = video_dir
        self.progress_file = video_dir / 'progress.json'
        self.progress = self._load_progress()
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load existing progress or create new"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'created_at': datetime.now().isoformat(),
            'stages_completed': [],
            'current_stage': None,
            'errors': []
        }
    
    def mark_stage_complete(self, stage_name: str):
        """Mark a pipeline stage as complete"""
        if stage_name not in self.progress['stages_completed']:
            self.progress['stages_completed'].append(stage_name)
        self.progress['current_stage'] = stage_name
        self.progress['last_updated'] = datetime.now().isoformat()
        self._save_progress()
    
    def add_error(self, stage_name: str, error_message: str):
        """Log an error for a stage"""
        self.progress['errors'].append({
            'stage': stage_name,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        })
        self._save_progress()
    
    def _save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2)
    
    def is_stage_complete(self, stage_name: str) -> bool:
        """Check if a stage has been completed"""
        return stage_name in self.progress['stages_completed']


# Utility functions

def resolve_project_path(path: Union[str, Path]) -> Path:
    """Resolve a path relative to the project root unless absolute."""
    path = Path(path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path

def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if necessary"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_timestamp() -> str:
    """Get formatted timestamp for file naming"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"
