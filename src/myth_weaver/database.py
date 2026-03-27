import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from myth_weaver.models import Base, Message, Campaign, Character

logger = logging.getLogger(__name__)

def get_db_session():
    """Initializes the PostgreSQL connection and returns a session."""
    user = os.getenv("POSTGRES_USER", "mythweaver")
    password = os.getenv("POSTGRES_PASSWORD", "devpassword")
    db = os.getenv("POSTGRES_DB", "mythweaver")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(db_url)
    
    # Ensure tables exist
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

class DatabaseManager:
    """Manages SQLAlchemy sessions and handles CRUD operations."""
    def __init__(self, session, campaign_id=None):
        self.session = session
        self.campaign_id = campaign_id

    def add(self, entity):
        self.session.add(entity)
        
    def commit(self):
        self.session.commit()
        
    def rollback(self):
        self.session.rollback()

    def get_recent_history(self, campaign_id: int, limit: int = 5) -> list[Message]:
        try:
            messages = (
                self.session.query(Message)
                .filter(Message.campaign_id == campaign_id)
                .order_by(Message.id.desc())
                .limit(limit)
                .all()
            )
            return messages[::-1]
        except Exception as e:
            logger.error("Failed to retrieve recent history: %s", {"error": str(e), "campaign_id": campaign_id})
            raise

    def get_current_state(self):
        """Fetches current game state and party details for LLM injection."""
        party_data = []
        if self.campaign_id:
            characters = self.session.query(Character).filter_by(campaign_id=self.campaign_id).all()
            for char in characters:
                party_data.append({
                    "name": char.name,
                    "hp": char.hp or 10,
                    "max_hp": char.max_hp or 10,
                    "description": char.description or ""
                })

        return {
            "location": "The Broken Anvil Tavern", # We will make location dynamic later
            "time_of_day": "Late Evening",
            "party": party_data,
            "npcs": "Bartender (Neutral)"
        }
    
    def get_active_milestone(self):
        """Fetches the active objective from the Campaign Bible."""
        if not self.campaign_id:
            return "Survive and explore."
            
        campaign = self.session.query(Campaign).filter_by(id=self.campaign_id).first()
        if campaign and campaign.campaign_bible:
            milestones = campaign.campaign_bible.get("milestones", [])
            for m in milestones:
                if not m.get("is_completed"):
                    return m.get("objective", "Unknown objective")
        return "Explore the world."

    def get_all_campaigns(self) -> list[Campaign]:
        """
        Fetches a list of all saved campaigns. 
        Orders them descending by ID so the most recent is first.
        """
        try:
            return (
                self.session.query(Campaign)
                .order_by(Campaign.id.desc())
                .all()
            )
        except Exception as e:
            logger.error("Failed to retrieve campaigns: %s", {"error": str(e)})
            raise