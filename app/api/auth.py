from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, ForgotPassword, ResetPassword
from app.schemas.token import Token, VerifyOTP
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.email import enviar_email_otp, enviar_email_recuperacao
from app.core.limiter import limiter
from app.core.logger import logger
import random
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
def register_user(request: Request, user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
@limiter.limit("5/minute")
def verify_otp(request: Request, data: VerifyOTP, db: Session = Depends(get_db)):
    logger.info(f"Tentativa de verificação de OTP para: {data.email}")
    
    utilizador = db.query(User).filter(User.email == data.email).first()
    
    if not utilizador:
        logger.warning(f"Verificação falhou: Utilizador não encontrado ({data.email})")
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    
    if utilizador.is_verified:
        logger.warning(f"Verificação falhou: Conta já ativada ({data.email})")
        raise HTTPException(status_code=400, detail="Esta conta já está verificada.")
        
    if utilizador.otp_code != data.otp:
        logger.warning(f"Verificação falhou: Código OTP inválido inserido ({data.email})")
        raise HTTPException(status_code=400, detail="Código inválido.")
        
    if utilizador.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        logger.warning(f"Verificação falhou: Código OTP expirado ({data.email})")
        raise HTTPException(status_code=400, detail="Este código já expirou. Peça um novo.")
        
    # Sucesso
    utilizador.is_verified = True
    utilizador.otp_code = None
    utilizador.otp_expiry = None
    db.commit()
    
    logger.success(f"Conta verificada com sucesso: {data.email}")
    return {"message": "Conta ativada com sucesso!"}

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request,form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # O form_data.username guarda o e-mail no padrão OAuth2
    logger.info(f"Tentativa de login para o usuário: {form_data.username}")
    
    utilizador = db.query(User).filter(User.email == form_data.username).first()
    if not utilizador or not verify_password(form_data.password, utilizador.hashed_password):
        logger.warning(f"Falha de login: Credenciais inválidas para {form_data.username}")
        raise HTTPException(status_code=401, detail="E-mail ou palavra-passe incorretos.")
        
    if not utilizador.is_verified:
        logger.warning(f"Falha de login: Conta não verificada para {form_data.username}")
        raise HTTPException(status_code=403, detail="Verifique o seu e-mail antes de fazer login.")
        
    access_token = create_access_token(data={"sub": str(utilizador.id)})
    
    logger.success(f"Login efetuado com sucesso: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, data: ForgotPassword, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"Pedido de recuperação de palavra-passe para: {data.email}")
    
    usuario = db.query(User).filter(User.email == data.email).first()
    
    if not usuario:
        # Registamos o aviso nos logs, mas não avisamos o atacante na resposta da API
        logger.info(f"Recuperação solicitada para e-mail inexistente: {data.email}")
        return {"message": "Se o e-mail estiver registado, receberá as instruções em breve."}
        
    codigo_otp = str(random.randint(100000, 999999))
    usuario.otp_code = codigo_otp
    usuario.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    
    background_tasks.add_task(enviar_email_recuperacao, usuario.email, codigo_otp, usuario.nome)
    
    logger.success(f"E-mail de recuperação gerado e colocado na fila para: {data.email}")
    return {"message": "Se o e-mail estiver registado, receberá as instruções em breve."}

@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, data: ResetPassword, db: Session = Depends(get_db)):
    logger.info(f"Tentativa de redefinição de palavra-passe para: {data.email}")
    
    usuario = db.query(User).filter(User.email == data.email).first()
    
    if not usuario:
        logger.warning(f"Reset falhou: Utilizador não encontrado ({data.email})")
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
        
    if usuario.otp_code != data.otp:
        logger.warning(f"Reset falhou: Código OTP inválido ({data.email})")
        raise HTTPException(status_code=400, detail="Código inválido.")
        
    if usuario.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        logger.warning(f"Reset falhou: Código OTP expirado ({data.email})")
        raise HTTPException(status_code=400, detail="Este código já expirou. Solicite um novo.")
        
    # Sucesso
    usuario.hashed_password = get_password_hash(data.new_password)
    usuario.otp_code = None
    usuario.otp_expiry = None
    db.commit()
    
    logger.success(f"Palavra-passe redefinida com sucesso para: {data.email}")
    return {"message": "Palavra-passe alterada com sucesso! Já pode fazer login."}