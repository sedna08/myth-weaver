import pytest
from unittest.mock import MagicMock, patch
import rollforge

@pytest.fixture
def mock_db_session():
    """Provides a mocked SQLAlchemy session for testing state injection and persistence."""
    session = MagicMock()
    return session

@pytest.fixture
def mock_ollama():
    """Mocks the Ollama client globally to avoid actual API calls during testing."""
    # Patch the chat function directly at the library level
    with patch("ollama.chat") as mock_chat:
        mock_module = MagicMock()
        mock_module.chat = mock_chat
        yield mock_module

@pytest.fixture
def seeded_rollforge():
    """Provides a deterministic RollForge environment."""
    rollforge.Dice.seed(42)
    return rollforge