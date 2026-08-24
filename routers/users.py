from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import User, UserProfile
from schemas.user_schema import ProfileCreate, ProfileResponse, ProfileUpdate, UserProfile as UserProfileResponse, UserUpdate
from utils.security import verify_token

router = APIRouter(prefix="/users", tags=["users"])
profiles_router = APIRouter(prefix="/profiles", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


@router.post("/profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    if current_user.profile is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A profile already exists for this user.")

    profile = UserProfile(
        user_id=current_user.user_id,
        full_name=payload.full_name,
        phone=payload.phone,
        address=payload.address,
        bio=payload.bio,
        profile_picture=payload.profile_picture,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        phone=profile.phone,
        address=profile.address,
        bio=profile.bio,
        profile_picture=profile.profile_picture,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    if current_user.profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    profile = current_user.profile
    return ProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        phone=profile.phone,
        address=profile.address,
        bio=profile.bio,
        profile_picture=profile.profile_picture,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )


@router.put("/profile", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    if current_user.profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    profile = current_user.profile
    if payload.full_name is not None:
        profile.full_name = payload.full_name
    if payload.phone is not None:
        profile.phone = payload.phone
    if payload.address is not None:
        profile.address = payload.address
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.profile_picture is not None:
        profile.profile_picture = payload.profile_picture

    db.commit()
    db.refresh(profile)
    return ProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        phone=profile.phone,
        address=profile.address,
        bio=profile.bio,
        profile_picture=profile.profile_picture,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )


@router.delete("/profile")
def delete_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.profile is not None:
        db.delete(current_user.profile)
    db.delete(current_user)
    db.commit()
    return {"message": "User account deleted successfully."}


@profiles_router.post("/me", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile_alias(payload: ProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    return create_profile(payload, current_user, db)


@profiles_router.get("/me", response_model=ProfileResponse)
def get_profile_alias(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    return get_profile(current_user, db)


@profiles_router.put("/me", response_model=ProfileResponse)
def update_profile_alias(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    return update_profile(payload, current_user, db)


@profiles_router.delete("/me")
def delete_profile_alias(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return delete_profile(current_user, db)
