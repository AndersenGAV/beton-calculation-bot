import asyncio

from aiogram import Bot, Dispatcher

from app.config import load_settings
from app.handlers.calculator import router as calculator_router
from app.handlers.start import router as start_router


async def main() -> None:
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()

    dispatcher.include_router(start_router)
    dispatcher.include_router(calculator_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())