from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.my_sql_config import Base


class Profile(Base):
    """
    SQLAlchemy model for user profiles.
    This model represents the profile table in the database.
    """
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False, comment="User identifier")
    username = Column(String(255), nullable=False)
    date_of_birth = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    education = Column(String(255), nullable=True)
    mother_tongue = Column(String(100), nullable=True)
    gender = Column(String(50), nullable=True)
    learning_pace = Column(String(50), nullable=True)
    
    # Metadata fields
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id}, username={self.username})>"

