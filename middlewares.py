from database.database import DataBase

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.dispatcher.flags import get_flag

from typing import Any, Awaitable, Callable, Dict


class DBMiddleware(BaseMiddleware):
    def __init__(self, database) -> None:
        self.db = database
    
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]
                       ) -> Any:
        
        if get_flag(data, 'database'):
            # data['db'] = self.db # Нужно это тут или лишнее?
            async with self.db.pool.acquire() as conn:
                data['conn'] = conn
                return await handler(event, data)
        return await handler(event, data)