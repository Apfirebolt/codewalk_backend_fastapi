from fastapi import APIRouter, status, HTTPException, Depends, Query
from typing import List, Optional
from . import schema, services
from auth.jwt import get_current_user
import auth.schema as auth_schema

router = APIRouter(tags=['Content (Blog, Projects, Gallery)'], prefix='/api/content')

@router.post('/', response_model=schema.ContentItemResponse, status_code=status.HTTP_201_CREATED)
async def create_content_item(
    request: schema.ContentItemCreate,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Create a new Blog, Project, or Gallery item with Editor.js content"""
    # Use user ID from JWT token authentication
    return await services.create_new_content(user_id=current_user.id, request=request)


@router.get('/', response_model=List[schema.ContentItemResponse])
async def get_all_content_items(
    content_type: Optional[schema.ContentType] = Query(None, description="Filter by blog, project, or gallery")
):
    """List all content items, optionally filtered by type"""
    return await services.fetch_all_content(content_type=content_type)


@router.get('/{slug}', response_model=schema.ContentItemResponse)
async def get_content_item_by_slug(slug: str):
    """Get a specific content item by its URL slug (auto increments view count)"""
    return await services.fetch_content_by_slug(slug)


@router.put('/{item_id}', response_model=schema.ContentItemResponse)
async def update_content_item(
    item_id: int,
    request: schema.ContentItemUpdate,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Update an existing content item (Blog, Project, or Gallery)"""
    return await services.modify_content(item_id=item_id, request=request)


@router.delete('/{item_id}')
async def delete_content_item(
    item_id: int,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Delete a content item by ID"""
    return await services.remove_content(item_id=item_id)