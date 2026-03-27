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

def test_db_04_get_all_campaigns(test_db_session):
    """Ensure the DatabaseManager can fetch a list of all saved campaigns."""
    from myth_weaver.database import DatabaseManager
    from myth_weaver.models import Campaign
    
    manager = DatabaseManager(test_db_session)
    
    # Arrange: Create two dummy campaigns satisfying the NOT NULL title constraint
    c1 = Campaign(title="Fantasy", campaign_bible={"campaign_name": "The Old Kingdom"})
    c2 = Campaign(title="Sci-Fi", campaign_bible={"campaign_name": "Neon Horizon"})
    manager.add(c1)
    manager.add(c2)
    manager.commit()
    
    # Act: Attempt to fetch them
    campaigns = manager.get_all_campaigns()
    
    # Assert
    assert len(campaigns) >= 2
    names = [c.campaign_bible.get("campaign_name") for c in campaigns if c.campaign_bible]
    assert "The Old Kingdom" in names
    assert "Neon Horizon" in names

def test_db_05_get_debug_state(test_db_session):
    """Ensure the DatabaseManager can fetch a unified debug state for the monitor."""
    from myth_weaver.database import DatabaseManager
    from myth_weaver.models import Campaign, Character, Message
    
    manager = DatabaseManager(test_db_session)
    
    # Arrange: Setup a campaign with a character and a message
    c = Campaign(title="Monitor Test", campaign_bible={"milestones": [{"objective": "Test the monitor", "is_completed": False}]})
    manager.add(c)
    manager.commit()
    
    char = Character(campaign_id=c.id, name="Observer", hp=10, max_hp=10)
    msg = Message(campaign_id=c.id, role="user", content="I look around.")
    
    manager.add(char)
    manager.add(msg)
    manager.commit()
    
    # Act: Fetch the debug state
    debug_state = manager.get_debug_state(c.id)
    
    # Assert
    assert "milestone" in debug_state
    assert debug_state["milestone"] == "Test the monitor"
    
    assert "characters" in debug_state
    assert len(debug_state["characters"]) == 1
    assert debug_state["characters"][0]["name"] == "Observer"
    
    assert "recent_messages" in debug_state
    assert len(debug_state["recent_messages"]) == 1
    assert debug_state["recent_messages"][0]["content"] == "I look around."