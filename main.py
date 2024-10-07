from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.context import FSMContext

from config import Config
from handlers.handlers import router
from middlewares import DBMiddleware
from database.database import DataBase

import asyncio


async def main() -> None:

    config = Config()

    db = DataBase(server=config.db.server,
                  database=config.db.database,
                  port=int(config.db.port),
                  username=config.db.username,
                  password=config.db.password)
    db.pool = await db.create_pool()

    storage = MemoryStorage()

    bot = Bot(token=config.bot.token)
    dp = Dispatcher(storage=storage)

    dp.include_router(router)
    dp.message.middleware(DBMiddleware(database=db))
    dp.callback_query.middleware(DBMiddleware(database=db))
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=[])


if __name__ == '__main__':
    asyncio.run(main())
