"""
User model for authentication.
Stores user credentials and authentication information.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.my_sql_config import Base
import uuid


class User(Base):
    """
    SQLAlchemy model for users.
    This model represents the users table in the database.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()), comment="Unique user identifier")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="User email address")
    hashed_password = Column(String(255), nullable=False, comment="Hashed password")
    
    # Metadata fields
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether the user account is active")
    is_verified = Column(Boolean, default=False, nullable=False, comment="Whether the user email is verified")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True, comment="Last login timestamp")

    def __repr__(self):
        return f"<User(id={self.id}, uuid={self.uuid}, email={self.email})>"

