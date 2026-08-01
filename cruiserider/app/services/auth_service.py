from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import user_repository
from app.models.users import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.security.password import hash_password, verify_password
from datetime import datetime, timedelta, timezone
from app.security.jwt import (
    create_access_token,
    create_refresh_token
)
class AuthService:
    def __init__(self):
        self.user_repository =user_repository

    async def register_user(
            self,
            db:AsyncSession,
            request: RegisterRequest
    ) -> User:
    
        existing_user = await self.user_repository.get_by_email(
            db,
            request.email
        )   
        if existing_user:
            raise ValueError("Email Already registered")
        
        password_hash = hash_password(request.password)

        user = User(
            name=request.name,
            email=request.email,
            password_hash=password_hash
        ) 
        return await self.user_repository.create(
            db,
            user
        )

    async def login_user(
            self,
            db: AsyncSession,
            request: LoginRequest

    ) -> TokenResponse:
        user = await self.user_repository.get_by_email(
            db,
            request.email
        )

        if not user:
            raise ValueError("Invalid Email or Password")

        if not verify_password(
            request.password,
            user.password_hash
        ):
            raise ValueError("Invalid Email or Password")
        if not user.is_active:
            raise ValueError("User account is inactive")
        user.last_login = datetime.now(timezone.utc)

        access_token =create_access_token(
            data={
                "sub": user.id,
                "role": user.role.value 
            }
        )
        refresh_token = create_refresh_token(
            data={
                "sub":user.id,
                "role": user.role.value 
            }
        )
        await db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
auth_service=AuthService()