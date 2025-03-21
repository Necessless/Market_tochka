from fastapi import FastAPI 
import uvicorn
from sqlalchemy import text
from core.config import settings
from api import router as api_router
from core.database import db_helper


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Сервер запущен"}

app.include_router(
    api_router,
    prefix = settings.api.prefix,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host = settings.run.host, 
        port = settings.run.port,
        reload = True)
    
