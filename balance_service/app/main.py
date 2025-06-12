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
from consumers.balance_deposit_consumer import start_consumer as start_deposit_consumer
from consumers.balance_withdraw_consumer import start_consumer as start_withdraw_consumer
from consumers.balance_remove_balance_consumer import start_consumer as start_remove_balance_consumer
from consumers.balance_unfreeze_consumer import start_consumer as start_unfreeze_balance_consumer
from consumers.balance_retriever_consumer import start_consumer as start_balance_retrieve_consumer
from producers.transaction_response_producer import producer as transaction_producer
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
    await transaction_producer.connect()
    yield  #back to work cycle
    for task in consumer_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    #app shutdown
    consumer_tasks.clear()
    await transaction_producer.close()
    await db_helper.dispose()

consumer_tasks = []


async def connect_with_rabbit():
    await asyncio.sleep(10)  
    consumer_tasks.append(asyncio.create_task(start_user_consumer()))
    consumer_tasks.append(asyncio.create_task(start_instrument_consumer()))
    consumer_tasks.append(asyncio.create_task(start_deposit_consumer()))
    consumer_tasks.append(asyncio.create_task(start_withdraw_consumer()))
    consumer_tasks.append(asyncio.create_task(start_remove_balance_consumer()))
    consumer_tasks.append(asyncio.create_task(start_unfreeze_balance_consumer()))
    consumer_tasks.append(asyncio.create_task(start_balance_retrieve_consumer()))

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
    
