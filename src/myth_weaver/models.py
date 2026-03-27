from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Use a variant to support JSONB in PostgreSQL (Prod) and JSON in SQLite (Testing)
CampaignJSON = JSON().with_variant(JSONB, 'postgresql')

class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    current_setting = Column(String)
    campaign_bible = Column(CampaignJSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    characters = relationship("Character", back_populates="campaign", cascade="all, delete-orphan")
    npcs = relationship("NPC", back_populates="campaign", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="campaign", order_by="Message.timestamp", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    name = Column(String, nullable=False)
    hp = Column(Integer)
    max_hp = Column(Integer)
    armor_class = Column(Integer)
    passive_perception = Column(Integer)
    attributes = Column(CampaignJSON)

    campaign = relationship("Campaign", back_populates="characters")


class NPC(Base):
    __tablename__ = 'npcs'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    name = Column(String, nullable=False)
    current_location = Column(String)
    status = Column(String)

    campaign = relationship("Campaign", back_populates="npcs")


class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    role = Column(String, nullable=False)  # e.g., 'user', 'dm', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    campaign = relationship("Campaign", back_populates="messages")