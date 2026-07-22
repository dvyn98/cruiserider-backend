from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


class UserRepository:

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> User | None:

        result = await db.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()


    async def get_by_id(
        self,
        db: AsyncSession,
        user_id: str
    ) -> User | None:

        result = await db.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()


    async def create(
        self,
        db: AsyncSession,
        user: User
    ) -> User:

        db.add(user)

        await db.flush()      # Sends INSERT to DB
        await db.refresh(user)

        return user


user_repository = UserRepository()