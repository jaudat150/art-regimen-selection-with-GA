# utils/helpers.py
"""
General-purpose helper functions used across the system.

Design principles:
  - No external dependencies (pure Python)
  - Fail-safe operations (graceful degradation)
  - Clinician-friendly outputs
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Any, List


_logger = logging.getLogger(__name__)


def strip_emoji(text: str) -> str:
    """Remove common emoji characters from text.

    Keeps most non-emoji Unicode (e.g., Arabic). Uses a conservative
    regex covering common emoji ranges.
    """
    try:
        import re

        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\u2600-\u26FF"  # misc symbols
            "\u2700-\u27BF"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r"", text)
    except Exception:
        return text


def format_duration(seconds: float) -> str:
    """
    Format elapsed time into human-readable string.
    
    Examples:
        0.56 -> "0.6s"
        62.3 -> "1m 2.3s"
        3661 -> "1h 1m 1s"
    
    Args:
        seconds (float): Elapsed time in seconds
    
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.1f}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}h {m}m {s:.1f}s"


def is_interactive_environment() -> bool:
    """
    Detect if running in an interactive environment (Jupyter, IPython, etc.)
    
    Used to decide whether to call plt.show().
    
    Returns:
        bool: True if interactive
    """
    try:
        # Prefer IPython detection when available
        from IPython import get_ipython
        ip = get_ipython()
        if ip is not None:
            name = ip.__class__.__name__
            return name in ('ZMQInteractiveShell', 'TerminalInteractiveShell')
    except Exception:
        pass

    # Fallback: check if stdin is a tty
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def validate_excel_file(filepath: str, required_sheets: List[str] = None) -> bool:
    """
    Validate Excel file structure for clinical data.
    
    Checks:
      - File exists
      - Required sheets present
      - Critical columns exist
      - No empty required cells
    
    Args:
        filepath (str): Path to Excel file
        required_sheets (list): List of required sheet names
    
    Returns:
        bool: True if valid
    """
    p = Path(filepath)
    if not p.exists():
        _logger.error("File not found: %s", filepath)
        return False

    try:
        import pandas as pd

        # Check sheets
        xls = pd.ExcelFile(p)
        if required_sheets:
            missing_sheets = [s for s in required_sheets if s not in xls.sheet_names]
            if missing_sheets:
                _logger.error("Missing sheets in %s: %s", filepath, missing_sheets)
                return False

        # If the file appears to be a drugs file (by sheet or filename), validate Drugs sheet
        if 'drugs' in p.stem.lower() or 'drugs' in [s.lower() for s in xls.sheet_names]:
            try:
                df = pd.read_excel(p, sheet_name='Drugs')
            except Exception:
                _logger.error("Drugs sheet missing or unreadable in %s", filepath)
                return False

            required_cols = ['Drug', 'Class', 'Efficacy', 'Toxicity', 'Monthly_Cost_USD']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                _logger.error("Missing columns in Drugs sheet: %s", missing_cols)
                return False

            # Check for empty Drug names
            empty_drugs = df[df['Drug'].isna() | (df['Drug'] == '')]
            if not empty_drugs.empty:
                _logger.warning("%d rows with empty Drug names in %s", len(empty_drugs), filepath)

        return True
    except Exception as e:
        _logger.exception("Error validating %s", filepath)
        return False


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Safe division with zero-division handling.
    
    Args:
        a (float): Numerator
        b (float): Denominator
        default (float): Value to return if b == 0
    
    Returns:
        float: a / b or default
    """
    try:
        return a / b if b != 0 else default
    except Exception:
        return default


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text with ellipsis for display.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
    
    Returns:
        str: Truncated text
    """
    return (text[:max_length] + '...') if len(text) > max_length else text