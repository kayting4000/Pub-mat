from sqlalchemy import select

from app.core.config import settings
from app.core.database_pg import AsyncSessionLocal
from app.core.security import hash_password
from app.models.sql_models import RoleEnum, User


async def seed_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        if result.scalar_one_or_none():
            return
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role=RoleEnum.editor_in_chief,
        )
        db.add(admin)
        await db.commit()
