import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.users import User, UserRole
from app.security.password import hash_password


ADMIN_NAME = "Priyanshu"
ADMIN_EMAIL = "divyanshurajputnbd@gmail.com"
ADMIN_PASSWORD = "Cruise123"


async def seed_admin():

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        )

        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin already exists.")
            return

        admin = User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )

        db.add(admin)

        await db.commit()

        await db.refresh(admin)

        print("Admin created successfully.")


if __name__ == "__main__":
    asyncio.run(seed_admin())