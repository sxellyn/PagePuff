from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import connect_db
from app.model.user_model import User
from app.schema.user_schema import AddUser
import bcrypt

router = APIRouter()

@router.post("/register")
def register_user(user: AddUser, db: Session = Depends(connect_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-mail already registred.")

    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_pw.decode("utf-8")
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}
