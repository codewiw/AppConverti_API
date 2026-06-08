from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY" )
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Desencripta o token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Vai à base de dados procurar o utilizador correspondente ao ID do token
    utilizador = db.query(User).filter(User.id == int(user_id)).first()
    if utilizador is None:
        raise credentials_exception
        
    return utilizador