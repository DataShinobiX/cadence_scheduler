from sqlalchemy import Column, String, Integer, Date, Time, TIMESTAMP, JSON, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    description = Column(String, nullable=False)
    original_input = Column(String)
    task_type = Column(String(50), default="user_requested")
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"))
    priority = Column(Integer, default=5)
    status = Column(String(50), default="pending")
    scheduled_date = Column(Date)
    start_time = Column(Time)
    duration_minutes = Column(Integer)
    deadline = Column(TIMESTAMP)
    location = Column(String(255))
    attendees = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String))
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)