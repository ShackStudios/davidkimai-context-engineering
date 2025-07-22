"""File handling utilities for the context engineering framework."""

import json
import yaml
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import shutil
import hashlib
from .logger import Logger
from .validator import Validator


class FileHandler:
    """Handles file operations for the framework."""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.logger = Logger("FileHandler")
        self.validator = Validator()
        
        # Create subdirectories
        self.agents_dir = self.base_dir / "agents"
        self.memory_dir = self.base_dir / "memory"
        self.context_dir = self.base_dir / "context"
        self.temp_dir = self.base_dir / "temp"
        self.backup_dir = self.base_dir / "backups"
        
        for dir_path in [self.agents_dir, self.memory_dir, self.context_dir, self.temp_dir, self.backup_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def save_json(self, data: Dict[str, Any], file_path: Union[str, Path], create_backup: bool = True) -> bool:
        """Save data as JSON file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path)
            
            # Create backup if file exists
            if create_backup and file_path.exists():
                self._create_backup(file_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"JSON data saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON to {file_path}: {e}")
            return False
    
    def load_json(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path, must_exist=True)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.debug(f"JSON data loaded from {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load JSON from {file_path}: {e}")
            return None
    
    def save_yaml(self, data: Dict[str, Any], file_path: Union[str, Path], create_backup: bool = True) -> bool:
        """Save data as YAML file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path)
            
            # Create backup if file exists
            if create_backup and file_path.exists():
                self._create_backup(file_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2, allow_unicode=True)
            
            self.logger.info(f"YAML data saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save YAML to {file_path}: {e}")
            return False
    
    def load_yaml(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load data from YAML file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path, must_exist=True)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            self.logger.debug(f"YAML data loaded from {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load YAML from {file_path}: {e}")
            return None
    
    def save_text(self, text: str, file_path: Union[str, Path], create_backup: bool = True) -> bool:
        """Save text to file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path)
            
            # Create backup if file exists
            if create_backup and file_path.exists():
                self._create_backup(file_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.logger.debug(f"Text saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save text to {file_path}: {e}")
            return False
    
    def load_text(self, file_path: Union[str, Path]) -> Optional[str]:
        """Load text from file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path, must_exist=True)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            self.logger.debug(f"Text loaded from {file_path}")
            return text
            
        except Exception as e:
            self.logger.error(f"Failed to load text from {file_path}: {e}")
            return None
    
    def save_pickle(self, data: Any, file_path: Union[str, Path], create_backup: bool = True) -> bool:
        """Save data as pickle file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path)
            
            # Create backup if file exists
            if create_backup and file_path.exists():
                self._create_backup(file_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            
            self.logger.debug(f"Pickle data saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save pickle to {file_path}: {e}")
            return False
    
    def load_pickle(self, file_path: Union[str, Path]) -> Optional[Any]:
        """Load data from pickle file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path, must_exist=True)
            
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            self.logger.debug(f"Pickle data loaded from {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load pickle from {file_path}: {e}")
            return None
    
    def _create_backup(self, file_path: Path):
        """Create backup of existing file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Backup created: {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    def get_file_hash(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get MD5 hash of file."""
        try:
            file_path = Path(file_path)
            self.validator.validate_file_path(file_path, must_exist=True)
            
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Failed to get hash for {file_path}: {e}")
            return None
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists."""
        return Path(file_path).exists()
    
    def delete_file(self, file_path: Union[str, Path], create_backup: bool = True) -> bool:
        """Delete file with optional backup."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                return True
            
            # Create backup before deletion
            if create_backup:
                self._create_backup(file_path)
            
            file_path.unlink()
            self.logger.info(f"File deleted: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified hours."""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            deleted_count = 0
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} temporary files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {e}")
    
    def get_directory_size(self, directory: Union[str, Path]) -> int:
        """Get total size of directory in bytes."""
        directory = Path(directory)
        total_size = 0
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to get directory size for {directory}: {e}")
            return 0
    
    def list_files(self, directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """List files in directory."""
        try:
            directory = Path(directory)
            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))
            
            # Filter to only files (not directories)
            files = [f for f in files if f.is_file()]
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    def ensure_directory(self, directory: Union[str, Path]) -> bool:
        """Ensure directory exists."""
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {directory}: {e}")
            return False
