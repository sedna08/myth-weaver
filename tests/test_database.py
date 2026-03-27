import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# These imports will fail until we build models.py and database.py
from myth_weaver.models import Base, Campaign, Character, NPC, Message
from myth_weaver.database import DatabaseManager

@pytest.fixture
def test_db_session():
    """Provides a fresh, in-memory SQLite database session for testing models."""
    # We use SQLite for fast unit testing, though prod uses PostgreSQL
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

def test_db_01_campaign_persistence(test_db_session):
    # Arrange
    bible_data = {
        "milestones": [{"chapter": 1, "objective": "Find the tavern", "is_completed": False}]
    }
    campaign = Campaign(
        title="Test Adventure", 
        current_setting="Dark Forest",
        campaign_bible=bible_data
    )
    
    # Act
    test_db_session.add(campaign)
    test_db_session.commit()
    
    # Assert
    saved_campaign = test_db_session.query(Campaign).first()
    assert saved_campaign is not None
    assert saved_campaign.title == "Test Adventure"
    # Validates JSONB/JSON serialization works
    assert saved_campaign.campaign_bible["milestones"][0]["objective"] == "Find the tavern"

def test_db_02_npc_tracking(test_db_session):
    # Arrange
    campaign = Campaign(title="NPC Test")
    test_db_session.add(campaign)
    test_db_session.commit()
    
    bartender = NPC(
        campaign_id=campaign.id,
        name="Bob the Bartender",
        current_location="The Prancing Pony",
        status="Suspicious"
    )
    
    # Act
    test_db_session.add(bartender)
    test_db_session.commit()
    
    # Assert
    saved_npc = test_db_session.query(NPC).filter_by(name="Bob the Bartender").first()
    assert saved_npc.campaign.title == "NPC Test"
    assert saved_npc.status == "Suspicious"

def test_db_03_message_history_sliding_window(test_db_session):
    # Arrange
    campaign = Campaign(title="History Test")
    test_db_session.add(campaign)
    test_db_session.commit()
    
    db_manager = DatabaseManager(test_db_session)
    
    # Act - Add 6 messages
    for i in range(6):
        msg = Message(
            campaign_id=campaign.id, 
            role="user" if i % 2 == 0 else "dm", 
            content=f"Message {i}"
        )
        test_db_session.add(msg)
    test_db_session.commit()
    
    # Assert - We only want the last 5 messages for the LLM context window
    history = db_manager.get_recent_history(campaign.id, limit=5)
    assert len(history) == 5
    assert history[0].content == "Message 1"
    assert history[-1].content == "Message 5"