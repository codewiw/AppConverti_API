import sys
from loguru import logger

# Remove o log padrão do Loguru para não duplicar com o Uvicorn
logger.remove()

# Configura a saída no terminal (colorida e formatada)
logger.add(
    sys.stdout, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.add(
    "logs/api_{time:YYYY-MM-DD}.log", 
    rotation="10 MB", 
    retention="10 days", 
    level="INFO",
    enqueue=True # Torna seguro para múltiplas threads/workers
)