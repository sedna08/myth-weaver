import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from myth_weaver.cli import cli, start_game

@pytest.fixture
def runner():
    """Provides a Click CliRunner for invoking commands in isolation."""
    return CliRunner()

def test_cli_help_menu(runner):
    """Ensure the base CLI group registers and displays help."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Myth Weaver: LLM Dungeon Master" in result.output

@patch("myth_weaver.cli.get_db_session")
@patch("myth_weaver.cli.generate_campaign_bible")
def test_cli_start_game_command(mock_generate, mock_get_db, runner):
    """Test the 'start' command triggers campaign generation and engine loop."""
    # Arrange
    mock_get_db.return_value = MagicMock()
    mock_generate.return_value = {"campaign_name": "Test Realm"}
    
    # Act
    result = runner.invoke(start_game, ["--theme", "Dark Fantasy"])
    
    # Assert
    assert result.exit_code == 0
    mock_generate.assert_called_once()
    # Update the expected string to match our new CLI output
    assert "Generating the Dark Fantasy Campaign Bible" in result.output

@patch("myth_weaver.cli.get_db_session")
@patch("myth_weaver.cli.handle_active_hint")
@patch("myth_weaver.cli.generate_campaign_bible")
def test_cli_processes_hint_command(mock_generate, mock_handle_hint, mock_get_db, runner):
    """Test that submitting /hint within the game loop triggers the hint system."""
    # Arrange
    mock_get_db.return_value = MagicMock()
    mock_generate.return_value = {"campaign_name": "Hint Realm"}
    mock_handle_hint.return_value = "A mysterious glow emanates from the floorboards..."
    
    # Act
    result = runner.invoke(start_game, ["--theme", "High Magic"], input="/hint\nquit\n")
    
    # Assert
    mock_handle_hint.assert_called_once()
    assert "A mysterious glow" in result.output