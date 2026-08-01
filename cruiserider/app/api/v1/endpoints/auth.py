from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import(
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse
)
from app.services.auth_service import auth_service

router = APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)

async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user= await auth_service.register_user(
            db,
            request
        )

        await db.commit()
        return user
    except ValueError as e:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/login",
    response_model=TokenResponse,

) 
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try: 
        return await auth_service.login_user(
            db,
            request
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )