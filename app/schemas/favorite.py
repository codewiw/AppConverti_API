from pydantic import BaseModel
from datetime import datetime

class FavoriteCreate(BaseModel):
    from_currency: str
    to_currency: str

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    from_currency: str
    to_currency: str
    created_at: datetime

    class Config:
        from_attributes = True