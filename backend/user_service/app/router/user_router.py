import bcrypt
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.config.database import connect_db
from app.config.auth import get_current_user
from app.model.user_model import User
from app.schema.user_schema import AddUser

router = APIRouter()

CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_AVATAR_BYTES = 2 * 1024 * 1024


@router.get("/avatar/{user_id}")
def get_avatar(user_id: int, db: Session = Depends(connect_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.avatar_blob is None or not user.avatar_mime:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return Response(
        content=user.avatar_blob,
        media_type=user.avatar_mime,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "has_avatar": current_user.avatar_blob is not None
        and current_user.avatar_mime is not None,
    }


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(connect_db),
    current_user: User = Depends(get_current_user),
):
    content_type = (file.content_type or "").split(";")[0].strip()
    if content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid image type. Use JPEG, PNG or WebP.",
        )
    data = await file.read()
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Image too large (max 2 MB).",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    current_user.avatar_blob = data
    current_user.avatar_mime = content_type
    db.commit()
    db.refresh(current_user)
    return {"has_avatar": True}


@router.delete("/me/avatar")
def delete_avatar(
    db: Session = Depends(connect_db),
    current_user: User = Depends(get_current_user),
):
    current_user.avatar_blob = None
    current_user.avatar_mime = None
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "has_avatar": False}


@router.post("/register")
def register_user(user: AddUser, db: Session = Depends(connect_db)):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
        new_user = User(
            username=user.username,
            email=user.email,
            password=hashed_pw.decode("utf-8"),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "username": new_user.username}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )
