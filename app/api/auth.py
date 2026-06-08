from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, ForgotPassword, ResetPassword
from app.schemas.token import Token, VerifyOTP
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.email import enviar_email_otp, enviar_email_recuperacao
import random
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Verifica se o e-mail já existe
    utilizador_existente = db.query(User).filter(User.email == user.email).first()
    if utilizador_existente:
        raise HTTPException(status_code=400, detail="Este e-mail já está registado.")

    # Gera o código de 6 dígitos e o tempo limite
    codigo_otp = str(random.randint(100000, 999999))
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Cria o utilizador com a palavra-passe encriptada
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

    # Envia o e-mail em segundo plano para não bloquear a resposta do servidor
    background_tasks.add_task(enviar_email_otp, novo_utilizador.email, codigo_otp, novo_utilizador.nome)

    return novo_utilizador

@router.post("/verify")
def verify_otp(data: VerifyOTP, db: Session = Depends(get_db)):
    utilizador = db.query(User).filter(User.email == data.email).first()
    
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    
    if utilizador.is_verified:
        raise HTTPException(status_code=400, detail="Esta conta já está verificada.")
        
    if utilizador.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Código inválido.")
        
    # Certifica-se de comparar tempos no mesmo fuso (UTC)
    if utilizador.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Este código já expirou. Peça um novo.")
        
    # Marca como verificado e limpa o OTP
    utilizador.is_verified = True
    utilizador.otp_code = None
    utilizador.otp_expiry = None
    db.commit()
    
    return {"message": "Conta ativada com sucesso!"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # O form_data.username guarda o e-mail no padrão OAuth2
    utilizador = db.query(User).filter(User.email == form_data.username).first()
    
    # Valida e-mail e palavra-passe
    if not utilizador or not verify_password(form_data.password, utilizador.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou palavra-passe incorretos.")
        
    # Impede login de quem não validou o e-mail
    if not utilizador.is_verified:
        raise HTTPException(status_code=403, detail="Verifique o seu e-mail antes de fazer login.")
        
    # Gera o Token embutindo o ID do utilizador
    access_token = create_access_token(data={"sub": str(utilizador.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == data.email).first()
    
    # Por motivos de segurança devolvemos sempre sucesso, mesmo se o e-mail não existir
    if not usuario:
        return {"message": "Se o e-mail estiver registado, receberá as instruções em breve."}
        
    # Gera um novo código OTP e define a validade (10 minutos)
    codigo_otp = str(random.randint(100000, 999999))
    usuario.otp_code = codigo_otp
    usuario.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    
    # Dispara o e-mail de recuperação em background
    background_tasks.add_task(enviar_email_recuperacao, usuario.email, codigo_otp, usuario.nome)
    
    return {"message": "Se o e-mail estiver registado, receberá as instruções em breve."}

@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == data.email).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
    if usuario.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Código inválido.")
        
    if usuario.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Este código já expirou. Solicite um novo.")
        
    # Criptografa a nova senha, limpa o OTP e salva.
    usuario.hashed_password = get_password_hash(data.new_password)
    usuario.otp_code = None
    usuario.otp_expiry = None
    db.commit()
    
    return {"message": "Senha alterada com sucesso! Já pode fazer login."}