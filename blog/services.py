from fastapi import HTTPException, status
from typing import List, Optional
from . import schema, models
import blog.db as blog_db

async def create_new_content(user_id: int, request: schema.ContentItemCreate) -> models.ContentItem:
    try:
        data = request.dict(exclude={"tag_names"})
        tags = request.tag_names or []
        return await blog_db.create_content(user_id=user_id, data=data, tag_names=tags)
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