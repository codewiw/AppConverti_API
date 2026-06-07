from fastapi import FastAPI
from app.db.database import engine, Base

# Ao iniciar, cria as tabelas automaticamente no Postgres caso não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Converti", version="1.0.0")

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "banco_de_dados": "conectado",
        "mensagem": "Motor FastAPI rodando com sucesso!"
    }