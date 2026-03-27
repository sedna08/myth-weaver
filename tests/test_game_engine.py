from myth_weaver.game_engine import (
    prepare_storyteller_prompt, 
    handle_active_hint, 
    check_passive_hints
)

def test_sys_05_state_injection(mock_db_session):
    # Arrange
    mock_db_session.get_current_state.return_value = {
        "location": "Tavern",
        "time_of_day": "Night",
        "player_current_hp": 25,
        "player_max_hp": 30,
        "npcs": "Bartender (Suspicious)"
    }
    mock_db_session.get_active_milestone.return_value = "Find the missing map"
    
    intent_summary = "Look around the room"
    rollforge_result = "No mechanical action required."

    # Act
    prompt = prepare_storyteller_prompt(
        mock_db_session, 
        intent_summary=intent_summary, 
        rollforge_result=rollforge_result
    )

    # Assert
    assert "Player HP: 25 / 30" in prompt, "Player HP was not correctly injected."
    assert "Find the missing map" in prompt, "Active milestone context is missing."
    assert "Bartender (Suspicious)" in prompt, "NPC state was not injected."

def test_sys_06_hint_system_active(mock_ollama, mock_db_session):
    # Arrange
    expected_hint = "The bartender is wiping down a glass, looking nervously at the floorboards."
    mock_ollama.chat.return_value = {"message": {"content": expected_hint}}
    
    # Act
    response = handle_active_hint(mock_db_session)

    # Assert
    assert mock_ollama.chat.called, "Storyteller was not bypassed to request a hint."
    assert response == expected_hint

def test_sys_07_hint_system_passive(mock_db_session, seeded_rollforge):
    # Arrange
    mock_db_session.turns_since_milestone = 11  # Exceeds the > 10 threshold
    player_passive_perception = 15
    
    # Act
    triggered, directive = check_passive_hints(
        turns=mock_db_session.turns_since_milestone, 
        perception_score=player_passive_perception
    )
    
    # Assert
    assert isinstance(triggered, bool)
    if triggered:
        assert "passive perception has noticed something" in directive.lower()