from myth_weaver.intent_parser import parse_intent

def test_sys_02_intent_parser_combat(mock_ollama):
    # Arrange
    user_input = "I swing my longsword at the goblin."
    mock_ollama.chat.return_value = {
        "message": {
            "content": '{"action_type": "combat", "target": "goblin", "tool_or_weapon": "longsword", "intent_summary": "Attack goblin", "requires_rollforge": true}'
        }
    }

    # Act
    result = parse_intent(user_input)

    # Assert
    assert result["action_type"] == "combat"
    assert result["target"] == "goblin"
    assert result["requires_rollforge"] is True

def test_sys_03_intent_parser_dialogue(mock_ollama):
    # Arrange
    user_input = "I ask the bartender about the missing map."
    mock_ollama.chat.return_value = {
        "message": {
            "content": '{"action_type": "dialogue", "target": "bartender", "tool_or_weapon": null, "intent_summary": "Ask about map", "requires_rollforge": false}'
        }
    }

    # Act
    result = parse_intent(user_input)

    # Assert
    assert result["action_type"] == "dialogue"
    assert result["requires_rollforge"] is False