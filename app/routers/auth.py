from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_payload,
    hash_password,
    revoke_access_token,
    verify_password,
)
from ..database import get_db
from ..errors import AppError
from ..models import Organization, User
from ..schemas import LoginRequest, RefreshRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.name == payload.org_name).first()
    role = "admin" if org is None else "member"
    
    if org is None:
        org = Organization(name=payload.org_name)
        db.add(org)
        db.commit()
        db.refresh(org)

    existing = (
        db.query(User)
        .filter(User.org_id == org.id, User.username == payload.username)
        .first()
    )
    if existing is not None:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            error_code="USERNAME_TAKEN",
            message="Username is already registered within this organization"
        )

    password_str = (
        payload.password.get_secret_value() 
        if hasattr(payload.password, "get_secret_value") 
        else payload.password
    )

    user = User(
        org_id=org.id,
        username=payload.username,
        hashed_password=hash_password(password_str),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "user_id": user.id,
        "org_id": org.id,
        "username": user.username,
        "role": user.role,
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.name == payload.org_name).first()
    user = None
    
    if org is not None:
        user = (
            db.query(User)
            .filter(User.org_id == org.id, User.username == payload.username)
            .first()
        )
        
    password_str = (
        payload.password.get_secret_value() 
        if hasattr(payload.password, "get_secret_value") 
        else payload.password
    )

    if user is None or not verify_password(password_str, user.hashed_password):
        raise AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid username or password")
        
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    
    if data.get("type") != "refresh":
        raise AppError(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Wrong token type")
        
    user_id_raw = data.get("sub")
    if not user_id_raw or not str(user_id_raw).isdigit():
        raise AppError(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Malformed token claims")

    user = db.query(User).filter(User.id == int(user_id_raw)).first()
    if user is None:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Unknown user")
        
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(payload: dict = Depends(get_token_payload)):
    revoke_access_token(payload)
    return {"status": "ok"}
