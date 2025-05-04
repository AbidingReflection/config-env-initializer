import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
from pathlib import Path


class CustomFormatter(logging.Formatter):
    """Custom formatter with optional microsecond-level timestamp precision."""

    def __init__(self, fmt=None, datefmt=None, use_microseconds=False):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_microseconds = use_microseconds

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        if self.use_microseconds:
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def prepare_logger(
    log_path: Path,
    output_name_prefix: str = "",
    use_microseconds: bool = False,
    log_level: str = "INFO"
) -> Logger:
    """
    Create a logger with both console and rotating file handlers.

    Args:
        log_path (Path): Directory to store log files.
        output_name_prefix (str): Optional prefix for the log filename.
        use_microseconds (bool): Whether to include microseconds in timestamp.
        log_level (str): Logging level (e.g., DEBUG, INFO, WARNING).

    Returns:
        Logger: Configured logger instance.
    """
    log_path.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    log_file = log_path / f"{output_name_prefix}{timestamp_str}.log"

    logger_name = f"config_logger_{output_name_prefix or 'default'}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.hasHandlers():
        return logger  # Avoid attaching multiple handlers on re-import

    log_format = CustomFormatter(
        fmt="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S.%f",
        use_microseconds=use_microseconds
    )

    # Console handler (INFO+ by default)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)

    # Rotating file handler (always full DEBUG level)
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
