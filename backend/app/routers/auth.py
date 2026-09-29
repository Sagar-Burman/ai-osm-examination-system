from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.deps import require_roles

from app.core.security import verify_password, create_access_token
from app.db.database import SessionLocal
from app.models.user import User
from app.schemas.auth import LoginResponse



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.username == form_data.username)
        .first()
    )

    if user is None or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

from fastapi import Body
from passlib.context import CryptContext
from app.models.user import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


@router.post("/users")
def create_user(
    username: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    current_user: dict = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db)
):
    if role not in {
        "operator",
        "examiner",
        "moderator",
        "admin"
    }:
        raise HTTPException(
            status_code=422,
            detail="Invalid role"
        )

    existing = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    user = User(
        username=username,
        password_hash=pwd_context.hash(password),
        role=role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active
    }