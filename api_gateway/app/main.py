from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from config import settings
from routes.users_router import router as users_router 
from routes.balance_router import router as balances_router
from routes.order_router import router as orders_router
from producers.base_producer import user_producer, instrument_producer

main_app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #app startup
    await user_producer.connect()
    await instrument_producer.connect()
    yield  #back to work cycle
    await user_producer.close()
    await instrument_producer.close()


@main_app.get("/")
async def root():
    print(settings.model_dump())
    return {"message": "Сервер запущен"}

main_app.include_router(users_router, prefix=settings.api.prefix)
main_app.include_router(balances_router, prefix=settings.api.prefix)
main_app.include_router(orders_router, prefix=settings.api.prefix)
if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", 
        host=settings.run.host, 
        port=settings.run.port,
        reload=True)
    
