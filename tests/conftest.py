"""Shared test configuration and fixtures."""

import os

# Set environment variables before any src imports
os.environ.setdefault("NARAMARKET_SERVICE_KEY", "test_service_key")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing")

# Patch missing OUTPUT_DIR in config before modules that depend on it are imported
import src.core.config as _config
if not hasattr(_config, "OUTPUT_DIR"):
    _config.OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "output")
