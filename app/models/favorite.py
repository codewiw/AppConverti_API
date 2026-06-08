from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    # A chave estrangeira que liga este favorito ao utilizador dono dele
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    from_currency = Column(String(5), nullable=False) # Ex: USD
    to_currency = Column(String(5), nullable=False)   # Ex: EUR
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())