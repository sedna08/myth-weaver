import pytest
from unittest.mock import MagicMock, patch

# This will fail because cli.py is empty
from myth_weaver.cli import process_user_input

@patch("myth_weaver.cli.handle_active_hint")
def test_cli_processes_hint_command(mock_handle_hint):
    # Arrange
    db_session = MagicMock()
    mock_handle_hint.return_value = "A mysterious glow emanates from the floorboards..."

    # Act
    # The CLI should intercept commands starting with '/' and route them appropriately
    response = process_user_input("/hint", db_session)

    # Assert
    mock_handle_hint.assert_called_once_with(db_session)
    assert response == "A mysterious glow emanates from the floorboards..."

@patch("myth_weaver.cli.parse_intent")
@patch("myth_weaver.cli.prepare_storyteller_prompt")
def test_cli_processes_standard_action(mock_prepare_prompt, mock_parse_intent):
    # Arrange
    db_session = MagicMock()
    # Mocking the Intent Parser returning a non-mechanic dialogue action
    mock_parse_intent.return_value = {
        "action_type": "dialogue", 
        "requires_rollforge": False, 
        "intent_summary": "Talk to the guard"
    }
    mock_prepare_prompt.return_value = "System prompt constructed."

    # Act
    process_user_input("I say hello to the guard.", db_session)

    # Assert
    mock_parse_intent.assert_called_once_with("I say hello to the guard.")
    mock_prepare_prompt.assert_called_once()