from typing import Optional

from sqlalchemy import select

from db import AsyncSessionLocal
from models import User


async def get_user_by_email(email: str) -> Optional[User]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def create_user(email: str, password_hash: str, name: Optional[str] = None) -> None:
    async with AsyncSessionLocal() as db:
        db.add(User(email=email, name=name, password_hash=password_hash, email_verified=True))
        await db.commit()


async def set_password_and_verify(email: str, password_hash: str, name: Optional[str] = None) -> None:
    """Attach a password credential to an existing (e.g. Google-only) user row."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.password_hash = password_hash
            user.email_verified = True
        else:
            db.add(User(email=email, name=name, password_hash=password_hash, email_verified=True))
        await db.commit()


async def update_password(email: str, password_hash: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.password_hash = password_hash
            await db.commit()
