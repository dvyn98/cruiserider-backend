from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.users import User, UserRole
from app.security.password import hash_password


ADMIN_NAME = "Priyanshu"
ADMIN_EMAIL = "divyanshurajputnbd@gmail.com"
ADMIN_PASSWORD = "Cruise123"


def seed_admin():
    db: Session = SessionLocal()

    try:
        existing_admin = (
            db.query(User)
            .filter(User.email == ADMIN_EMAIL)
            .first()
        )

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
        db.commit()

        print("Admin created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()