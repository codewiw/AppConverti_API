from fastapi import FastAPI, Request
import time
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.logger import logger
from app.db.database import engine, Base
from app.models import user, favorite
from app.api import auth, favorites
from app.core.limiter import limiter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Converti", version="1.0.0")
app.include_router(auth.router)
app.include_router(favorites.router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    
    # Loga o IP, Método, Rota, Status e Tempo de Resposta (em milissegundos)
    logger.info(f"{request.client.host} - {request.method} {request.url.path} - Status: {response.status_code} - {formatted_process_time}ms")
    
    return response

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "mensagem": "Motor FastAPI rodando com sucesso!"
    }

