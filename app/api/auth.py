from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash
from app.core.email import enviar_email_otp
import random
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Verifica se o e-mail já existe
    utilizador_existente = db.query(User).filter(User.email == user.email).first()
    if utilizador_existente:
        raise HTTPException(status_code=400, detail="Este e-mail já está registado.")

    # 2. Gera o código de 6 dígitos e o tempo limite
    codigo_otp = str(random.randint(100000, 999999))
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=10)

    # 3. Cria o utilizador com a palavra-passe encriptada
    novo_utilizador = User(
        nome=user.nome,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        otp_code=codigo_otp,
        otp_expiry=expira_em
    )
    
    db.add(novo_utilizador)
    db.commit()
    db.refresh(novo_utilizador)

    # 4. Envia o e-mail em segundo plano para não bloquear a resposta do servidor
    background_tasks.add_task(enviar_email_otp, novo_utilizador.email, codigo_otp, novo_utilizador.nome)

    return novo_utilizador