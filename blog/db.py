from typing import List, Optional, Dict, Any
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from slugify import slugify  # pip install python-slugify

from config import db as sync_db
from . import models

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
        # Ensure unique slug
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
        db.refresh(new_item)
        return new_item
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _get_all_content_sync(content_type: Optional[str] = None) -> List[models.ContentItem]:
    db: Session = sync_db.SessionLocal()
    try:
        query = db.query(models.ContentItem)
        if content_type:
            query = query.filter(models.ContentItem.content_type == content_type)
        return query.order_by(models.ContentItem.date_posted.desc()).all()
    finally:
        db.close()

def _get_content_by_slug_sync(slug: str) -> Optional[models.ContentItem]:
    db: Session = sync_db.SessionLocal()
    try:
        item = db.query(models.ContentItem).filter(models.ContentItem.slug == slug).first()
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
        item = db.query(models.ContentItem).filter(models.ContentItem.id == item_id).first()
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
        db.delete(item)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Async wrappers using thread pool
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