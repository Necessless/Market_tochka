# ОСНОВНЫЕ ПРОБЛЕМЫ И ИСПРАВЛЕНИЯ:

"""
1. КРИТИЧЕСКАЯ ОШИБКА: Проверка результата саги НЕПРАВИЛЬНАЯ
   - Вы проверяете `if result is False:` но wait_for_all возвращает True/False/None
   - None означает таймаут или отсутствие correlation_id
   - False означает что хотя бы одна операция провалилась
   
2. RACE CONDITION в SagaTransactionStore
   - _locks создается через defaultdict, но register перезаписывает Event
   - Может привести к потере событий между потоками

3. НЕПРАВИЛЬНАЯ ЛОГИКА ОТКАТА
   - Нет реализации компенсирующих транзакций
   - После провала операций нужно откатывать уже выполненные

4. ПРОБЛЕМЫ С ОБРАБОТКОЙ ОШИБОК
   - В make_transaction_messages возвращается True даже при провале саги
   - Нет отката транзакции БД при провале саги
"""

# ИСПРАВЛЕННЫЙ KOД:

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Set
from collections import defaultdict
from enum import Enum

class OperationStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success" 
    FAILED = "failed"
    COMPENSATED = "compensated"

class SagaTransactionStore:
    def __init__(self):
        self._storage: Dict[str, Dict] = {}
        self._locks: Dict[str, asyncio.Event] = {}

    def register(self, correlation_id: str, operation_count: int = 4):
        """Регистрируем сагу с заданным количеством операций"""
        if correlation_id not in self._locks:
            self._locks[correlation_id] = asyncio.Event()
        
        self._storage[correlation_id] = {
            "results": {i: OperationStatus.PENDING for i in range(1, operation_count + 1)},
            "event": self._locks[correlation_id],
            "created_at": asyncio.get_event_loop().time()
        }

    def record_result(self, correlation_id: str, operation_id: int, success: bool):
        """Записываем результат операции"""
        if correlation_id not in self._storage:
            print(f"WARN: Получен результат для неизвестной саги {correlation_id}")
            return

        status = OperationStatus.SUCCESS if success else OperationStatus.FAILED
        self._storage[correlation_id]["results"][operation_id] = status
        
        print(f"Операция {operation_id} для саги {correlation_id}: {status.value}")

        # Проверяем завершение всех операций
        results = self._storage[correlation_id]["results"]
        if all(status != OperationStatus.PENDING for status in results.values()):
            self._locks[correlation_id].set()

    async def wait_for_all(self, correlation_id: str, timeout: float = 10.0) -> Optional[bool]:
        """Ждем завершения всех операций саги"""
        if correlation_id not in self._storage:
            return None
            
        try:
            await asyncio.wait_for(self._locks[correlation_id].wait(), timeout=timeout)
            
            results = self._storage[correlation_id]["results"]
            # Проверяем что все операции успешны
            all_success = all(status == OperationStatus.SUCCESS for status in results.values())
            return all_success
            
        except asyncio.TimeoutError:
            print(f"TIMEOUT для саги {correlation_id}")
            return False

    def get_failed_operations(self, correlation_id: str) -> List[int]:
        """Получаем список провалившихся операций"""
        if correlation_id not in self._storage:
            return []
        
        return [
            op_id for op_id, status in self._storage[correlation_id]["results"].items() 
            if status == OperationStatus.FAILED
        ]
    
    def get_successful_operations(self, correlation_id: str) -> List[int]:
        """Получаем список успешных операций для отката"""
        if correlation_id not in self._storage:
            return []
        
        return [
            op_id for op_id, status in self._storage[correlation_id]["results"].items() 
            if status == OperationStatus.SUCCESS
        ]

    def cleanup(self, correlation_id: str):
        """Очищаем данные саги"""
        self._storage.pop(correlation_id, None)
        self._locks.pop(correlation_id, None)

manager = SagaTransactionStore()