from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "sqlite:///./meetings.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)
    participants = Column(Text)  # Comma-separated list
    raw_notes = Column(Text, nullable=False)
    ai_summary = Column(Text)
    tags = Column(Text)  # Comma-separated list
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")


class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    description = Column(Text, nullable=False)
    owner = Column(String)
    due_date = Column(DateTime)
    status = Column(String, default="pending")  # pending, in_progress, completed
    created_at = Column(DateTime, default=func.now())
    
    meeting = relationship("Meeting", back_populates="action_items")


def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
