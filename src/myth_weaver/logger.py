import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    """
    Centralized logging configuration for the Myth Weaver application.
    Ensures logs are written to a file and rotated, with warnings printed to the console.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger('myth_weaver')
    
    # Avoid adding handlers multiple times if setup_logger is called repeatedly
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.DEBUG)

    # Rotating file handler to prevent infinite log growth
    file_handler = RotatingFileHandler(
        'logs/mythweaver.log', maxBytes=5*1024*1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler for critical/warning alerts during runtime
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger