import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Define a default log directory and file
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = __name__,
    level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    log_to_file: bool = True,
    log_to_console: bool = True,  # New parameter
    log_file_path: str = LOG_FILE,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
):
    """
    Configures and returns a logger instance.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
        log_format (str): The format string for log messages.
        date_format (str): The format string for the date/time in log messages.
        log_to_file (bool): Whether to log to a file.
        log_file_path (str): The full path to the log file.
        max_bytes (int): Maximum size of the log file before rotation.
        backup_count (int): Number of backup log files to keep.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Prevent adding multiple handlers if logger already configured
    if logger.hasHandlers():
        logger.handlers.clear()
        # Or, if you want to reconfigure existing handlers, you might need more complex logic.
        # For simplicity, we clear and re-add.
        # Alternatively, check if a handler of a specific type already exists.

    logger.setLevel(level)

    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Console Handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler (optional)
    if log_to_file:
        try:
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file_path}")
        except Exception as e:
            # Log to console if file logging setup fails
            logger.error(
                f"Failed to set up file logging to {log_file_path}: {e}", exc_info=True
            )

    # Set propagation to False if you don't want logs to go up to the root logger,
    # especially if the root logger has its own handlers.
    # logger.propagate = False

    return logger


if __name__ == "__main__":
    # Example usage:
    # Get a logger for the current module
    logger1 = setup_logger(__name__, level=logging.DEBUG)
    logger1.debug("This is a debug message from logger1.")
    logger1.info("This is an info message from logger1.")
    logger1.warning("This is a warning message from logger1.")

    # Get a logger for a different component/module
    another_logger = setup_logger(
        "another.component", level=logging.INFO, log_to_file=False
    )
    another_logger.info("Info message from another_logger (console only).")

    # Test log rotation (you'd need to generate >10MB of logs to see it rotate)
    # for i in range(100000):
    #    logger1.info(f"Test log message number {i} to fill up the log file for rotation testing.")
    print(f"Default log file should be at: {LOG_FILE}")
