from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.domain.models import ConcretePrice

NEW_CALCULATION_BUTTON_TEXT = "\u041d\u043e\u0432\u044b\u0439 \u0440\u0430\u0441\u0447\u0435\u0442"


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=NEW_CALCULATION_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
    )


def build_concrete_keyboard(items: list[ConcretePrice]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for index, item in enumerate(items):
        builder.button(text=item.short_label, callback_data=f"concrete:{index}")

    if items:
        builder.adjust(1)

    return builder.as_markup()


def build_back_keyboard(target: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=f"back:{target}")
    return builder.as_markup()
