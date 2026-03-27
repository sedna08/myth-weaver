import os
import pytest
from myth_weaver.logger import setup_logger

def test_logger_creates_directory_and_file(tmp_path, monkeypatch):
    """Ensure the logger creates the 'logs' directory and writes properly formatted logs."""
    # Arrange: Temporarily change the working directory so we don't pollute the real project root
    monkeypatch.chdir(tmp_path)
    
    # Act
    logger = setup_logger()
    logger.warning("A wild goblin appears!")
    
    # Assert
    assert os.path.exists("logs"), "The 'logs' directory was not created."
    assert os.path.exists("logs/mythweaver.log"), "The log file was not created."
    
    with open("logs/mythweaver.log", "r") as log_file:
        content = log_file.read()
        assert "A wild goblin appears!" in content
        assert "WARNING" in content
        assert "myth_weaver" in content