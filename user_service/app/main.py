from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from config import settings
from api.router import router 
from database import db_helper

@asynccontextmanager
async def lifespan(app: FastAPI):
    #app startup
    yield #back to work cycle
    #app shutdown
    await db_helper.dispose()


main_app = FastAPI(lifespan=lifespan)

@main_app.get("/")
async def root():
    return {"message": "User service is running"}

main_app.include_router(router, prefix=settings.api.prefix)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", 
        host=settings.run.host, 
        port=settings.run.port,
        reload=True)
    
