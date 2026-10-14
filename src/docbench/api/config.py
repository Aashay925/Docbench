"""
Configuration and environment settings for DocBench FastAPI REST Service.
"""

import os
import tempfile
from pathlib import Path
from typing import List

from docbench.config import PROJECT_ROOT, OUTPUTS_DIR


class ApiSettings:
    """API configuration loaded with environment variable overrides."""

    def __init__(self):
        # 5 MB default upload limit
        size_mb_env = os.getenv("DOCBENCH_MAX_UPLOAD_SIZE_MB")
        size_bytes_env = os.getenv("DOCBENCH_MAX_UPLOAD_SIZE_BYTES")
        if size_bytes_env:
            self.max_upload_size_bytes = int(size_bytes_env)
        elif size_mb_env:
            self.max_upload_size_bytes = int(float(size_mb_env) * 1024 * 1024)
        else:
            self.max_upload_size_bytes = 5 * 1024 * 1024

        # Temporary files directory
        temp_dir_env = os.getenv("DOCBENCH_TEMP_DIR")
        if temp_dir_env:
            self.temp_dir = Path(temp_dir_env).resolve()
        else:
            self.temp_dir = OUTPUTS_DIR / "temp"

        # CORS origins
        cors_env = os.getenv("DOCBENCH_CORS_ORIGINS", "*")
        if cors_env.strip() == "*":
            self.cors_origins: List[str] = ["*"]
        else:
            self.cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

        # Logging level
        self.log_level = os.getenv("DOCBENCH_LOG_LEVEL", "INFO").upper()

        # Version information
        self.app_version = "0.1.0"
        self.api_version = "v1"

    def ensure_temp_dir(self):
        """Ensure temporary directory exists."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)


api_settings = ApiSettings()
