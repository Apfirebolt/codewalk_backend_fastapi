from typing import List, Optional, Dict, Any
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session, joinedload, selectinload
from slugify import slugify
import os
import re
import cloudinary
from urllib.parse import urlparse
from config import db as sync_db
from . import models
from auth import models as auth_models


def _extract_cloudinary_public_id(url: str) -> Optional[str]:
    """Extracts Cloudinary public ID from a secure URL for deletion."""
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        if 'upload' in path_parts:
            upload_idx = path_parts.index('upload')
            relevant_parts = path_parts[upload_idx + 1:]
            
            # If there's a version string like 'v1711234567', skip it
            if relevant_parts and re.match(r'^v\d+$', relevant_parts[0]):
                relevant_parts = relevant_parts[1:]
                
            # Join remaining parts and strip extension
            full_path = "/".join(relevant_parts)
            public_id, _ = os.path.splitext(full_path)
            return public_id
    except Exception:
        pass
    return None


def _get_or_create_tags_sync(db: Session, tag_names: List[str]) -> List[models.Tag]:
    tags = []
    for name in tag_names:
        clean_name = name.strip().lower()
        if not clean_name:
            continue
        tag = db.query(models.Tag).filter(models.Tag.name == clean_name).first()
        if not tag:
            tag = models.Tag(name=clean_name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags

def _create_content_sync(user_id: int, data: Dict[str, Any], tag_names: List[str]) -> models.ContentItem:
    db: Session = sync_db.SessionLocal()
    try:
        base_slug = slugify(data["title"])
        slug = base_slug
        counter = 1
        while db.query(models.ContentItem).filter(models.ContentItem.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tags = _get_or_create_tags_sync(db, tag_names)

        new_item = models.ContentItem(
            user_id=user_id,
            title=data["title"],
            slug=slug,
            content_type=data["content_type"],
            content=data.get("content", {}),
            extra_metadata=data.get("extra_metadata", {}),
            meta_title=data.get("meta_title"),
            meta_description=data.get("meta_description"),
            is_published=data.get("is_published", False),
            tags=tags
        )
        db.add(new_item)
        db.commit()
        item_id = new_item.id
        db.close()

        # Re-query with joinedload in a fresh session
        db = sync_db.SessionLocal()
        return db.query(models.ContentItem).options(
            joinedload(models.ContentItem.tags)
        ).filter(models.ContentItem.id == item_id).first()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _get_all_content_sync(content_type: Optional[str] = None) -> List[models.ContentItem]:
    db: Session = sync_db.SessionLocal()
    try:
        query = db.query(models.ContentItem).options(joinedload(models.ContentItem.tags))
        if content_type:
            query = query.filter(models.ContentItem.content_type == content_type)
        return query.order_by(models.ContentItem.date_posted.desc()).all()
    finally:
        db.close()

def _get_content_by_slug_sync(slug: str) -> Optional[models.ContentItem]:
    db: Session = sync_db.SessionLocal()
    try:
        item = db.query(models.ContentItem).options(
            joinedload(models.ContentItem.tags)
        ).filter(models.ContentItem.slug == slug).first()
        
        if item:
            item.views += 1
            db.commit()
            db.refresh(item)
        return item
    finally:
        db.close()

def _update_content_sync(item_id: int, update_data: Dict[str, Any], tag_names: Optional[List[str]]) -> models.ContentItem:
    db: Session = sync_db.SessionLocal()
    try:
        item = db.query(models.ContentItem).options(
            joinedload(models.ContentItem.tags)
        ).filter(models.ContentItem.id == item_id).first()
        
        if not item:
            raise Exception("Content item not found")

        for key, value in update_data.items():
            if value is not None:
                setattr(item, key, value)
                
        if "title" in update_data and update_data["title"]:
            item.slug = slugify(update_data["title"])

        if tag_names is not None:
            item.tags = _get_or_create_tags_sync(db, tag_names)

        db.commit()
        db.refresh(item)
        return item
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _delete_content_sync(item_id: int) -> bool:
    db: Session = sync_db.SessionLocal()
    try:
        item = db.query(models.ContentItem).filter(models.ContentItem.id == item_id).first()
        if not item:
            return False

        # Extract all image URLs from Editor.js JSON content blocks
        content_data = item.content or {}
        blocks = content_data.get("blocks", [])
        image_urls = [
            block["data"]["file"]["url"]
            for block in blocks
            if block.get("type") == "image" and block.get("data", {}).get("file", {}).get("url")
        ]

        # Delete images from Cloudinary
        for url in image_urls:
            public_id = _extract_cloudinary_public_id(url)
            if public_id:
                try:
                    cloudinary.uploader.destroy(public_id, resource_type="image")
                except Exception as img_err:
                    print(f"Failed to delete image from Cloudinary ({public_id}): {img_err}")

        # Delete database record
        db.delete(item)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def is_user_admin(user_id: int) -> bool:
    db: Session = sync_db.SessionLocal()
    try:
        user = db.query(auth_models.User).filter(auth_models.User.id == user_id).first()
        if not user:
            return False
        return user.role == "admin"
    finally:
        db.close()


# --- COMMENT OPERATIONS ---

def _get_comments_by_content_id_sync(content_id: int) -> List[models.Comment]:
    db: Session = sync_db.SessionLocal()
    try:
        # Fetch all comments for this content item flatly, eager-loading the user relationship
        all_comments = db.query(models.Comment).filter(
            models.Comment.content_id == content_id
        ).options(
            joinedload(models.Comment.user)
        ).order_by(models.Comment.date_created.asc()).all()
        
        # Build dictionary map and construct the recursive tree in Python
        comment_map = {}
        top_level_comments = []

        for comment in all_comments:
            comment.replies = []  # Initialize empty replies list
            comment_map[comment.id] = comment

        for comment in all_comments:
            if comment.parent_id is None:
                top_level_comments.append(comment)
            else:
                parent = comment_map.get(comment.parent_id)
                if parent:
                    parent.replies.append(comment)

        # Sort top-level comments descending (newest first)
        top_level_comments.sort(key=lambda x: x.date_created, reverse=True)
        return top_level_comments
    finally:
        db.close()

def _create_comment_sync(content_id: int, user_id: int, body: str, parent_id: Optional[int] = None) -> models.Comment:
    db: Session = sync_db.SessionLocal()
    try:
        if parent_id:
            parent_comment = db.query(models.Comment).filter(models.Comment.id == parent_id).first()
            if not parent_comment:
                raise Exception("Parent comment not found")
            if parent_comment.content_id != content_id:
                raise Exception("Parent comment does not belong to this content item")

        comment = models.Comment(
            content_id=content_id,
            user_id=user_id,
            body=body,
            parent_id=parent_id
        )
        db.add(comment)
        db.commit()
        comment_id = comment.id
        db.close()

        # Re-open session and fetch with user eager-loaded
        db = sync_db.SessionLocal()
        created = db.query(models.Comment).options(
            joinedload(models.Comment.user)
        ).filter(models.Comment.id == comment_id).first()
        if created:
            created.replies = []
        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _update_comment_sync(comment_id: int, user_id: int, new_body: str) -> models.Comment:
    db: Session = sync_db.SessionLocal()
    try:
        comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        if not comment:
            raise Exception("Comment not found")
        if comment.user_id != user_id:
            raise Exception("Unauthorized to edit this comment")

        comment.body = new_body
        comment.is_edited = True
        db.commit()
        comm_id = comment.id
        db.close()

        db = sync_db.SessionLocal()
        updated = db.query(models.Comment).options(
            joinedload(models.Comment.user)
        ).filter(models.Comment.id == comm_id).first()
        if updated:
            updated.replies = []
        return updated
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _delete_comment_sync(comment_id: int, user_id: int, is_admin: bool = False) -> bool:
    db: Session = sync_db.SessionLocal()
    try:
        comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        if not comment:
            return False
        
        # Allow deletion if user owns the comment or is an admin
        if comment.user_id != user_id and not is_admin:
            raise Exception("Unauthorized to delete this comment")

        db.delete(comment)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# --- ASYNC WRAPPERS USING THREAD POOL ---

async def create_content(user_id: int, data: Dict[str, Any], tag_names: List[str]) -> models.ContentItem:
    return await run_in_threadpool(_create_content_sync, user_id, data, tag_names)

async def get_all_content(content_type: Optional[str] = None) -> List[models.ContentItem]:
    return await run_in_threadpool(_get_all_content_sync, content_type)

async def get_content_by_slug(slug: str) -> Optional[models.ContentItem]:
    return await run_in_threadpool(_get_content_by_slug_sync, slug)

async def update_content(item_id: int, update_data: Dict[str, Any], tag_names: Optional[List[str]]) -> models.ContentItem:
    return await run_in_threadpool(_update_content_sync, item_id, update_data, tag_names)

async def delete_content(item_id: int) -> bool:
    return await run_in_threadpool(_delete_content_sync, item_id)

async def get_comments_by_content_id(content_id: int) -> List[models.Comment]:
    return await run_in_threadpool(_get_comments_by_content_id_sync, content_id)

async def create_comment(content_id: int, user_id: int, body: str, parent_id: Optional[int] = None) -> models.Comment:
    return await run_in_threadpool(_create_comment_sync, content_id, user_id, body, parent_id)

async def update_comment(comment_id: int, user_id: int, new_body: str) -> models.Comment:
    return await run_in_threadpool(_update_comment_sync, comment_id, user_id, new_body)

async def delete_comment(comment_id: int, user_id: int, is_admin: bool = False) -> bool:
    return await run_in_threadpool(_delete_comment_sync, comment_id, user_id, is_admin)