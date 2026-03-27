import logging
from myth_weaver.models import Message

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages SQLAlchemy sessions and handles CRUD operations for the game engine.
    """
    def __init__(self, session):
        self.session = session

    def get_recent_history(self, campaign_id: int, limit: int = 5) -> list[Message]:
        """
        Retrieves the most recent messages for the conversation sliding window.
        """
        try:
            # Query the latest messages ordered by descending timestamp/id, limited by the threshold
            messages = (
                self.session.query(Message)
                .filter(Message.campaign_id == campaign_id)
                .order_by(Message.id.desc())
                .limit(limit)
                .all()
            )
            # Reverse the list so it is in chronological order for the LLM prompt
            return messages[::-1]
            
        except Exception as e:
            logger.error("Failed to retrieve recent history: %s", {"error": str(e), "campaign_id": campaign_id})
            raise