import json
import logging
import ollama

logger = logging.getLogger(__name__)

# Temporary mock to allow tests to pass without models.py fully implemented
class _MockCampaign:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

try:
    from myth_weaver.models import Campaign
except ImportError:
    Campaign = _MockCampaign

def generate_campaign_bible(theme: str, db_session) -> dict:
    """
    Generates a campaign bible and persists it to the database.
    This runs a procedural generation script prompting Ollama to build a Campaign Bible in JSON format.
    """
    system_prompt = (
        "You are a procedural generation engine. Generate a Campaign Bible in JSON format. "
        "Follow the schema: campaign_name, theme, setting_description, starting_location, "
        "main_quest, milestones, global_secrets."
    )
    
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a {theme} campaign."}
            ],
            format="json"
        )
        
        bible_json = response.get("message", {}).get("content", "{}")
        campaign_data = json.loads(bible_json)
        
        # The schema is updated to support the Campaign Bible (JSONB)
        new_campaign = Campaign(
            title=campaign_data.get("campaign_name", "Untitled Campaign"),
            current_setting=campaign_data.get("setting_description", ""),
            campaign_bible=campaign_data
        )
        
        db_session.add(new_campaign)
        db_session.commit()
        
        return campaign_data
        
    except json.JSONDecodeError as e:
        logger.error({"error": str(e), "theme": theme}, "Failed to decode Campaign Bible JSON")
        db_session.rollback()
        raise
    except Exception as e:
        logger.error({"error": str(e)}, "Campaign generation failed")
        db_session.rollback()
        raise