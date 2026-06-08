from fastapi import FastAPI
from app.db.database import engine, Base
from app.models import user, favorite
from app.api import auth, favorites

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Converti", version="1.0.0")

app.include_router(auth.router) 

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "mensagem": "Motor FastAPI rodando com sucesso!"
    }