"""
Robust environment setup for resource-limited settings.

Key features:
  - Works on headless servers (no GUI)
  - Creates directory structure for reports
  - UTF-8 encoding for Arabic support
  - Minimal disk space usage

Syria-specific considerations:
  - UTF-8 encoding for Arabic support
  - Minimal dependencies for restricted environments
"""

import os
import sys
import locale
import logging

_logger = logging.getLogger(__name__)


def setup_environment(output_dir: str = 'reports') -> str:
    """
    Set up the execution environment for HIV regimen optimization.
    
    Actions performed:
      1. Create output directory structure
      2. Set UTF-8 encoding for Arabic support (had problems with parsing them before)
      3. Log system information for support tickets
    
    Args:
        output_dir (str): Base directory for reports (default: 'reports')
    
    Returns:
        str: Absolute path to output directory
    """
    _logger.info("%s", "=" * 50)
    _logger.info("SETTING UP HIV REGIMEN OPTIMIZER")
    _logger.info("%s", "=" * 50)
    
    # === 1. Ensure output directory structure ===
    abs_output_dir = ensure_output_dir(output_dir)
    reports_dir = ensure_output_dir(os.path.join(output_dir, 'regimens'))
    
    _logger.info("Output directories:")
    _logger.info("  Reports: %s", reports_dir)
    
    # === 2. Set UTF-8 encoding (Arabic support) ===
    _setup_utf8_encoding()
    
    # === 4. Log system information ===
    _logger.info("System info:")
    _logger.info("  Python: %s", sys.version.split()[0])
    _logger.info("  Platform: %s", sys.platform)
    _logger.info("  PID: %s", os.getpid())

    _logger.info("%s", "=" * 50)
    return abs_output_dir


def ensure_output_dir(path: str) -> str:
    """
    Ensure a directory exists and return its absolute path.
    
    Safe for concurrent access (critical in multi-user clinics).
    
    Args:
        path (str): Directory path
    
    Returns:
        str: Absolute path to directory
    """
    try:
        os.makedirs(path, exist_ok=True)
        return os.path.abspath(path)
    except PermissionError:
        # Fallback to user's home directory (common in restricted clinics)
        fallback = os.path.expanduser(f"~/{os.path.basename(path)}")
        os.makedirs(fallback, exist_ok=True)
        _logger.warning("Warning: Using fallback directory: %s", fallback)
        return fallback


def _setup_utf8_encoding():
    """
    Set UTF-8 encoding for Arabic support in reports.
    
    Critical for Syria/MENA region deployments.
    """
    try:
        if hasattr(locale, 'setlocale'):
            locale.setlocale(locale.LC_ALL, 'ar_SY.UTF-8')
    except:
        pass  # Continue with default encoding
    
    # Ensure stdout/stderr use UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  