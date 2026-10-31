from fastapi import APIRouter, status, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from . import schema, services
from auth.jwt import get_current_user
import auth.schema as auth_schema
from utils.cloudinary_helper import upload_image_to_cloudinary

router = APIRouter(tags=['Content (Blog, Projects, Gallery)'], prefix='/api/content')

@router.post('/', response_model=schema.ContentItemResponse, status_code=status.HTTP_201_CREATED)
async def create_content_item(
    request: schema.ContentItemCreate,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Create a new Blog, Project, or Gallery item with Editor.js content"""
    return await services.create_new_content(user_id=current_user.id, request=request)


@router.get('/', response_model=List[schema.ContentItemResponse])
async def get_all_content_items(
    content_type: Optional[schema.ContentType] = Query(None, description="Filter by blog, project, or gallery")
):
    """List all content items, optionally filtered by type"""
    return await services.fetch_all_content(content_type=content_type)


@router.post('/upload-image')
async def upload_editor_image(
    file: UploadFile = File(...),
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Upload an inline image from Editor.js to Cloudinary via backend"""
    try:
        secure_url = await upload_image_to_cloudinary(file)
        return {
            "success": 1,
            "file": {
                "url": secure_url
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )


# --- COMMENT ENDPOINTS (Placed before /{slug} to avoid path parameter conflicts) ---

@router.get('/{content_id}/comments', response_model=List[schema.CommentResponse])
async def get_comments_for_content_item(content_id: int):
    """Fetch all top-level comments and nested replies for a specific content item"""
    return await services.fetch_comments_for_content(content_id=content_id)


@router.post('/{content_id}/comments', response_model=schema.CommentResponse, status_code=status.HTTP_201_CREATED)
async def post_comment_to_content(
    content_id: int,
    request: schema.CommentCreate,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Post a new comment or reply to a specific content item"""
    return await services.add_comment_to_content(
        content_id=content_id,
        user_id=current_user.id,
        request=request
    )


@router.put('/comments/{comment_id}', response_model=schema.CommentResponse)
async def update_comment_item(
    comment_id: int,
    request: schema.CommentUpdate,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Update an existing comment body (Owner only)"""
    return await services.modify_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        request=request
    )


@router.delete('/comments/{comment_id}')
async def delete_comment_item(
    comment_id: int,
    current_user: auth_schema.TokenData = Depends(get_current_user)
):
    """Delete a comment by ID (Owner or Admin)"""
    is_admin = getattr(current_user, "role", "user") == "admin"
    return await services.remove_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        is_admin=is_admin
    )


# --- GENERAL CONTENT ENDPOINTS ---

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