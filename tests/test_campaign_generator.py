import json
from myth_weaver.storyteller import generate_campaign_bible

def test_sys_01_campaign_generation(mock_db_session, mock_ollama):
    # Arrange
    theme = "Dark Fantasy"
    mock_response = {
        "campaign_name": "Shadows of Doom",
        "theme": theme,
        "setting_description": "A dark, unforgiving world.",
        "starting_location": {
            "name": "The Broken Anvil Tavern",
            "description": "A dingy, smell tavern.",
            "initial_npcs": ["npc_1"]
        },
        "main_quest": {
            "objective": "Survive the night",
            "antagonist": "The Night King",
            "stakes": "The end of the world"
        },
        "milestones": [
            {
                "chapter": 1,
                "objective": "Find the ancient sword",
                "is_completed": False,
                "key_locations": [],
                "trigger_events": []
            }
        ],
        "global_secrets": ["The king is secretly a vampire."]
    }
    
    # Mock the LLM returning a valid JSON string
    mock_ollama.chat.return_value = {"message": {"content": json.dumps(mock_response)}}

    # Act
    campaign_bible = generate_campaign_bible(theme, mock_db_session)

    # Assert
    assert mock_ollama.chat.called, "Ollama chat was not called to generate the campaign."
    assert campaign_bible["theme"] == theme, "The parsed JSON does not match the expected schema."
    assert mock_db_session.add.called, "Campaign was not added to the database session."
    assert mock_db_session.commit.called, "Database session was not committed."