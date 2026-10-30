from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from typing import Any
from config.db import Base
from . import hashing

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email = Column(String(255), unique=True)
    role = Column(String(50), nullable=True, default='user')
    password = Column(String(255))
    profile_image = Column(String(500), nullable=True)

    # Add this line to establish the back-population
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, username: str, email: str, role: str, password: str, first_name: str = None, last_name: str = None, profile_image: str = None, *args: Any, **kwargs: Any) -> None:
        self.username = username
        self.email = email
        self.role = role
        self.password = hashing.get_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.profile_image = profile_image

    def check_password(self, password: str) -> bool:
        return hashing.verify_password(password, self.password)