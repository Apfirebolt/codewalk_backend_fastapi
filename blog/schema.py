from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import ContentType

class TagBase(BaseModel):
    name: str
    description: Optional[str] = None

class TagResponse(TagBase):
    id: int
    date_created: datetime

    class Config:
        from_attributes = True

class ContentItemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content_type: ContentType
    content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    is_published: Optional[bool] = False
    tag_names: Optional[List[str]] = Field(default_factory=list) # Pass tag names directly

class ContentItemUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[Dict[str, Any]] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None
    tag_names: Optional[List[str]] = None

class ContentItemResponse(BaseModel):
    id: int
    user_id: int
    title: str
    slug: str
    content_type: ContentType
    content: Optional[Dict[str, Any]]
    extra_metadata: Optional[Dict[str, Any]]
    meta_title: Optional[str]
    meta_description: Optional[str]
    is_published: bool
    views: int
    date_posted: datetime
    date_updated: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


# --- COMMENT SCHEMAS ---

class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1, description="Comment body text")
    parent_id: Optional[int] = Field(None, description="ID of the parent comment if this is a nested reply")

class CommentUpdate(BaseModel):
    body: str = Field(..., min_length=1, description="Updated comment body text")

class AuthorResponse(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class CommentResponse(BaseModel):
    id: int
    content_id: int
    user_id: int
    parent_id: Optional[int] = None
    body: str
    date_created: datetime
    is_edited: bool
    user: Optional[AuthorResponse] = None
    replies: List['CommentResponse'] = []  # Recursively holds nested replies

    class Config:
        from_attributes = True

# Required for recursive self-referencing Pydantic models in Python
CommentResponse.model_rebuild()