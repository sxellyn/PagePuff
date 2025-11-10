from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import connect_db
from app.model.user_model import User
from app.schema.user_schema import AddUser, UserResponse
import bcrypt
from app.config.auth import get_current_user

router = APIRouter()

@router.post("/register")
def register_user(user: AddUser, db: Session = Depends(connect_db)):
    # Verificar se email já existe
    existing_user_by_email = db.query(User).filter(User.email == user.email).first()
    if existing_user_by_email:
        raise HTTPException(status_code=400, detail="Email já está registrado")
    
    # Verificar se username já existe
    existing_user_by_username = db.query(User).filter(User.username == user.username).first()
    if existing_user_by_username:
        raise HTTPException(status_code=400, detail="Nome de usuário já está em uso")

    try:
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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao registrar usuário: {str(e)}")

@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Retorna o perfil do usuário logado"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }
