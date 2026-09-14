from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import create_access_token, get_current_user, get_optional_user, hash_password, verify_password
from backend.models import User
from backend.schemas import AuthCredentials, AuthResponse, MessageResponse, UserResponse
from backend.store import store

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(credentials: AuthCredentials) -> AuthResponse:
    email = credentials.email.strip().lower()
    password = credentials.password

    if "@" not in email or len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use a valid email and a password with at least four characters.",
        )

    existing = store.get_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    hashed = hash_password(password)
    user = store.create_user(email=email, password_hash=hashed)
    token = create_access_token(user_id=user.id, email=user.email)

    return AuthResponse(
        id=user.id,
        email=user.email,
        token=token,
        user=UserResponse(id=user.id, email=user.email),
    )


@router.post("/login", response_model=AuthResponse)
def login(credentials: AuthCredentials) -> AuthResponse:
    email = credentials.email.strip().lower()
    password = credentials.password

    if not email or len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter an email and a password with at least four characters.",
        )

    user = store.get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        id=user.id,
        email=user.email,
        token=token,
        user=UserResponse(id=user.id, email=user.email),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Successfully signed out.")


@router.get("/session", response_model=Optional[UserResponse])
def get_session(current_user: Optional[User] = Depends(get_optional_user)) -> Optional[UserResponse]:
    if not current_user:
        return None
    return UserResponse(id=current_user.id, email=current_user.email)
