from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.keyboards.calculator import build_main_menu_keyboard

router = Router()

START_TEXT = (
    "\u041f\u0440\u0438\u0432\u0435\u0442! "
    "\u042d\u0442\u043e \u0431\u043e\u0442 \u0434\u043b\u044f "
    "\u0440\u0430\u0441\u0447\u0435\u0442\u0430 \u0441\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u0438 "
    "\u0431\u0435\u0442\u043e\u043d\u0430.\n\n"
    "\u041d\u0430\u0436\u043c\u0438 "
    "\"\u041d\u043e\u0432\u044b\u0439 \u0440\u0430\u0441\u0447\u0435\u0442\"."
)

HELP_TEXT = (
    "\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u044b:\n"
    "/start - \u0437\u0430\u043f\u0443\u0441\u043a \u0431\u043e\u0442\u0430\n"
    "/help - \u043f\u043e\u043c\u043e\u0449\u044c"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        START_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        HELP_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )