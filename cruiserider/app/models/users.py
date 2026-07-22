import uuid
import enum

from sqlalchemy import(
    Column,
    String,
    Boolean,
    DateTime,
    Enum
)
    
from sqlalchemy.sql import func
from app.core.database import Base
class UserRole(str,enum.Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER
    )

    is_active = Column(
        Boolean,
        default=True
    )

    last_login = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )