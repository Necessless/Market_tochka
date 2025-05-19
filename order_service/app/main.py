from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import time
from config import settings
from api.router import router 
from database import db_helper
import asyncio
from consumers.order_consumer import start_consumer as start_orders_consumer
from consumers.user_delete_consumer import start_consumer as start_users_consumer
from consumers.instrument_delete_consumer import start_consumer as start_instrument_consumer
@asynccontextmanager
async def lifespan(app: FastAPI):
    #app startup
    await connect_with_rabbit()
    yield #back to work cycle
    #app shutdown
    await db_helper.dispose()


async def connect_with_rabbit():
    time.sleep(7)
    await asyncio.create_task(start_orders_consumer())
    await asyncio.create_task(start_users_consumer())
    await asyncio.create_task(start_instrument_consumer())

main_app = FastAPI(lifespan=lifespan)

@main_app.get("/")
async def root():
    return {"message": "Order service is running"}

main_app.include_router(router, prefix=settings.api.prefix)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", 
        host=settings.run.host, 
        port=settings.run.port,
        reload=True)
    
