from fastapi import FastAPI
import uvicorn
from config import settings


main_app = FastAPI()

@main_app.get("/")
async def root():
    print(settings.model_dump())
    return {"message": "Сервер запущен"}



if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", 
        host=settings.run.host, 
        port=settings.run.port,
        reload=True)
    
