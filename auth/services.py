from fastapi import HTTPException, status
from typing import List, Optional

from . import schema
from . import models
from . import hashing
import auth.db as auth_db


async def new_user_register(request: schema.User) -> models.User:
    try:
        new_user = await auth_db.create_user(request.username, request.email, request.password, role='user')
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while registering the user: {str(e)}"
        )


async def all_users() -> List[models.User]:
    try:
        users = await auth_db.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching all users: {str(e)}"
        )


async def get_user_by_id(user_id: int) -> Optional[models.User]:
    try:
        user_info = await auth_db.get_user_by_id(user_id)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data not found!"
            )

        return user_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the user by ID: {str(e)}"
        )


async def get_profile(current_user: schema.TokenData) -> models.User:
    try:
        user = await auth_db.get_user_by_email(current_user.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the user profile: {str(e)}"
        )


async def update_user_profile(user_email: str, update_data: schema.UserUpdate) -> models.User:
    try:
        user = await auth_db.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await auth_db.update_user_details(user.id, update_data.dict(exclude_unset=True))
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating profile: {str(e)}"
        )


async def change_user_password(user_email: str, password_data: schema.ChangePassword) -> dict:
    try:
        user = await auth_db.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        if not hashing.verify_password(password_data.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
            
        new_hashed_password = hashing.get_password_hash(password_data.new_password)
        await auth_db.update_user_password(user.id, new_hashed_password)
        
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while changing password: {str(e)}"
        )


async def update_profile_image(user_email: str, image_url: str) -> models.User:
    try:
        user = await auth_db.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        updated_user = await auth_db.update_user_profile_image(user.id, image_url)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating profile image: {str(e)}"
        )