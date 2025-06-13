from api.service import deposit_on_balance
import json
from uuid import UUID
from aio_pika import ExchangeType, connect_robust, IncomingMessage
from config import settings
import asyncio
from schemas.balance_DTO import BalanceDTODirection, Deposit_Withdraw_Instrument_V1
from schemas.responses import Transaction_Response
from producers.transaction_response_producer import producer


RABBITMQ_URL = settings.rabbitmq.url
shutdown_event = asyncio.Event()


async def on_message(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body)
            correlation_id = data.pop("correlation_id")
            sub_id = data.pop("sub_id")
            direction = BalanceDTODirection[data.pop("direction")]
            user_id = UUID(data.pop("user_id"))
            balance_dto = Deposit_Withdraw_Instrument_V1(direction=direction, user_id=user_id, **data)
            await deposit_on_balance(balance_dto)
            await producer.publish_message(Transaction_Response(correlation_id=correlation_id, sub_id=sub_id, success=True))
        except Exception as e:
            print(f"Ошибка при обработке удаления тикера: {str(e)}")
            try:
                await producer.publish_message(Transaction_Response(correlation_id=correlation_id,sub_id=sub_id, success=False, message=str(e)))
            except Exception as e:
                print(f"[CRITICAL] Не удалось отправить сообщение об ошибке: {str(e)}")

async def start_consumer():
    delay = 3
    while True:
        connection = None
        try:
            connection = await connect_robust(RABBITMQ_URL, timeout=10)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            exchange = await channel.declare_exchange("Balance_change_exchange", ExchangeType.DIRECT, durable=True)
            queue = await channel.declare_queue("Balance_change_exchange.DEPOSIT", durable=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
                })
            await queue.bind(exchange, routing_key="DEPOSIT")
            await queue.consume(on_message)
            await shutdown_event.wait()
        except Exception:
            print("Ошибка при обработке транзакции депозита на баланс")
            await asyncio.sleep(delay)
            delay = min(delay*2, 30)
        finally:
            if connection and not connection.is_closed:
                await connection.close()
