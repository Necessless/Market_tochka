from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy import select
from models import Instrument
from config import settings
from api.router import router 
from database import db_helper
from consumers.user_delete_consumer import start_consumer as start_user_consumer
from consumers.instrument_delete_consumer import start_consumer as start_instrument_consumer
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    #app startup
    async with db_helper.async_session_factory() as session:
        query = select(Instrument).filter(Instrument.ticker == "RUB")
        result = await session.scalar(query)
        if not result: 
            rub_ticker = Instrument(ticker="RUB", name="Ruble")
            session.add(rub_ticker)
            await session.commit()
    await connect_with_rabbit()
    yield  #back to work cycle
    for task in consumer_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    #app shutdown
    await db_helper.dispose()

consumer_tasks = []


async def connect_with_rabbit():
    await asyncio.sleep(7)  
    consumer_tasks.append(asyncio.create_task(start_user_consumer()))
    consumer_tasks.append(asyncio.create_task(start_instrument_consumer()))


main_app = FastAPI(lifespan=lifespan)

@main_app.get("/")
async def root():
    return {"message": "Balance service is running"}

main_app.include_router(router, prefix=settings.api.prefix)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", 
        host=settings.run.host, 
        port=settings.run.port,
        reload=True)
    
