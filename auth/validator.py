from typing import Optional

from . import models
import auth.db as auth_db


async def verify_email_exist(email: str) -> Optional[models.User]:
    return await auth_db.get_user_by_email(email)
