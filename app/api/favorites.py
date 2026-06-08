from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/favorites", tags=["Favoritos"])

# Repare no "current_user". Isto obriga a requisição a ter um Token JWT válido!
@router.post("/", response_model=FavoriteResponse)
def create_favorite(
    favorite: FavoriteCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verifica se o utilizador já tem este par guardado (evita duplicados)
    existente = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.from_currency == favorite.from_currency,
        Favorite.to_currency == favorite.to_currency
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="Este par de moedas já está nos favoritos.")
        
    novo_favorito = Favorite(
        user_id=current_user.id,
        from_currency=favorite.from_currency.upper(),
        to_currency=favorite.to_currency.upper()
    )
    
    db.add(novo_favorito)
    db.commit()
    db.refresh(novo_favorito)
    return novo_favorito

@router.get("/", response_model=list[FavoriteResponse])
def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Devolve APENAS os favoritos do utilizador que fez o pedido
    favoritos = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    return favoritos

@router.delete("/{favorite_id}")
def delete_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Procura o favorito certificando-se de que pertence ao utilizador logado
    favorito = db.query(Favorite).filter(
        Favorite.id == favorite_id, 
        Favorite.user_id == current_user.id
    ).first()
    
    if not favorito:
        raise HTTPException(status_code=404, detail="Favorito não encontrado ou não lhe pertence.")
        
    db.delete(favorito)
    db.commit()
    return {"message": "Favorito removido com sucesso."}