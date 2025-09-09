import os
import tempfile
import hashlib
import json
from typing import Dict, List, Any, Optional
import time
import numpy as np

class Utils:
    @staticmethod
    def create_temp_file(suffix: str = ".mp4") -> str:
        """Create a temporary file with given suffix"""
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(temp_fd)
        return temp_path

    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Safely remove a temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {file_path}: {e}")

    @staticmethod
    def validate_video_file(file_path: str) -> bool:
        """Validate if a file is a valid video (simplified check)"""
        try:
            # Basic file validation - check extension and size
            valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
            ext = os.path.splitext(file_path)[1].lower()
            return ext in valid_extensions and os.path.getsize(file_path) > 1000
        except:
            return False

    # Additional utility methods for file handling, validation, etc.
