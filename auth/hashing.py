from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
import bcrypt


_ph = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _ph.verify(hashed_password, plain_password)
    except InvalidHash:
        try:
            if isinstance(hashed_password, str):
                return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
            return False
        except Exception:
            return False
    except (VerifyMismatchError, VerificationError):
        return False


def is_legacy_bcrypt_hash(hashed_password: str) -> bool:
    """Return True if the stored hash looks like a bcrypt hash (legacy)."""
    if not isinstance(hashed_password, str):
        return False
    # bcrypt hashes start with $2b$, $2a$, $2y$, etc.
    return hashed_password.startswith("$2")


def get_password_hash(password: str) -> str:
    return _ph.hash(password)
