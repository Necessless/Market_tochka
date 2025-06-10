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
from producers.order_producer import producer

shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    #app startup
    await connect_with_rabbit()
    await producer.connect()
    yield #back to work cycle
    #app shutdown
    shutdown_event.set()
    for task in consumer_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
    await producer.close()
    await db_helper.dispose()


consumer_tasks = []


async def connect_with_rabbit():
    await asyncio.sleep(10)  
    consumer_tasks.append(asyncio.create_task(start_orders_consumer()))
    consumer_tasks.append(asyncio.create_task(start_users_consumer()))
    consumer_tasks.append(asyncio.create_task(start_instrument_consumer()))

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
    
