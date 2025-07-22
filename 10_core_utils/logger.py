"""Enhanced logging system for context engineering framework."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class Logger:
    """Enhanced logger with context tracking and structured output."""
    
    def __init__(self, name: str = "context_engineering", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup formatters
        self._setup_formatters()
        self._setup_handlers()
        
        # Context tracking
        self.context_stack = []
        
    def _setup_formatters(self):
        """Setup log formatters."""
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    
    def _setup_handlers(self):
        """Setup log handlers."""
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON handler for structured logs
        json_file = self.log_dir / f"{self.name}_structured.json"
        json_handler = logging.FileHandler(json_file)
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        self.json_handler = json_handler
        self.logger.addHandler(json_handler)
    
    def push_context(self, context: Dict[str, Any]):
        """Push context onto the context stack."""
        self.context_stack.append(context)
        self.debug(f"Context pushed: {context}")
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from the context stack."""
        if self.context_stack:
            context = self.context_stack.pop()
            self.debug(f"Context popped: {context}")
            return context
        return None
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get the current context."""
        merged_context = {}
        for context in self.context_stack:
            merged_context.update(context)
        return merged_context
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured data."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'context': self.get_current_context(),
            **kwargs
        }
        
        # Log to JSON handler
        self.json_handler.emit(
            logging.LogRecord(
                name=self.name,
                level=getattr(logging, level.upper()),
                pathname='',
                lineno=0,
                msg=json.dumps(log_entry),
                args=(),
                exc_info=None
            )
        )
    
    def debug(self, message: str, **kwargs):
        """Debug level logging."""
        self.logger.debug(message)
        self._log_structured('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info level logging."""
        self.logger.info(message)
        self._log_structured('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging."""
        self.logger.warning(message)
        self._log_structured('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error level logging."""
        self.logger.error(message)
        self._log_structured('error', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical level logging."""
        self.logger.critical(message)
        self._log_structured('critical', message, **kwargs)
