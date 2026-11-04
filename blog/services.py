from fastapi import HTTPException, status
from typing import List, Optional
from . import schema, models
import blog.db as blog_db


async def create_new_content(user_id: int, request: schema.ContentItemCreate) -> models.ContentItem:
    try:
        data = request.dict(exclude={"tag_names"})
        tags = request.tag_names or []
        # only users with admin role can create new content
        if not blog_db.is_user_admin(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create new content"
            )
        return await blog_db.create_content(user_id=user_id, data=data, tag_names=tags)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating content item: {str(e)}"
        )

async def fetch_all_content(content_type: Optional[str] = None) -> List[models.ContentItem]:
    try:
        return await blog_db.get_all_content(content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching content items: {str(e)}"
        )

async def fetch_content_by_slug(slug: str) -> models.ContentItem:
    item = await blog_db.get_content_by_slug(slug)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content item not found"
        )
    return item

async def modify_content(item_id: int, request: schema.ContentItemUpdate) -> models.ContentItem:
    try:
        update_data = request.dict(exclude={"tag_names"}, exclude_unset=True)
        tag_names = request.tag_names
        updated = await blog_db.update_content(item_id, update_data, tag_names)
        return updated
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating content item: {str(e)}"
        )

async def remove_content(item_id: int) -> dict:
    success = await blog_db.delete_content(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content item not found"
        )
    return {"message": "Content item deleted successfully"}


# --- COMMENT SERVICES ---

async def add_comment_to_content(content_id: int, user_id: int, request: schema.CommentCreate) -> models.Comment:
    try:
        return await blog_db.create_comment(
            content_id=content_id,
            user_id=user_id,
            body=request.body,
            parent_id=request.parent_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to post comment: {str(e)}"
        )

async def fetch_comments_for_content(content_id: int) -> List[models.Comment]:
    try:
        return await blog_db.get_comments_by_content_id(content_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching comments: {str(e)}"
        )

async def modify_comment(comment_id: int, user_id: int, request: schema.CommentUpdate) -> models.Comment:
    try:
        return await blog_db.update_comment(
            comment_id=comment_id,
            user_id=user_id,
            new_body=request.body
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update comment: {str(e)}"
        )

async def remove_comment(comment_id: int, user_id: int, is_admin: bool = False) -> dict:
    try:
        success = await blog_db.delete_comment(comment_id, user_id, is_admin)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return {"message": "Comment deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete comment: {str(e)}"
        )