from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Text, Enum as SQLEnum, func, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from enum import Enum
from config.db import Base

# Enum for sections
class ContentType(str, Enum):
    BLOG = "blog"
    PROJECT = "project"
    GALLERY = "gallery"

# Many-to-many association table for tags
content_tags_association = Table(
    "content_tags_association",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("content_items.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True) # blog, project, gallery
    
    content = Column(JSONB, nullable=True, default=dict)
    
    extra_metadata = Column(JSONB, nullable=True, default=dict)
    
    # SEO fields
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Status & Analytics
    is_published = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    
    # Timestamps
    date_posted = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    tags = relationship("Tag", secondary=content_tags_association, back_populates="contents")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationship back to content items
    contents = relationship("ContentItem", secondary=content_tags_association, back_populates="tags")