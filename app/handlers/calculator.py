import asyncio
from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.keyboards.calculator import (
    build_back_keyboard,
    build_concrete_keyboard,
)
from app.services.google_sheets import (
    save_to_google_sheets,
    update_margin_in_google_sheets,
)
from app.services.price_loader import load_concrete_prices, load_delivery_prices
from app.states.calc_states import ConcreteCalculationStates


router = Router()

NEW_CALCULATION_TEXT = "Новый расчет"

MSG_PRICE_LOAD_FAILED = "Не удалось загрузить прайс. Проверь файл prices/prices.xlsx."
MSG_EMPTY_CONCRETE = "Список марок пуст. Проверь Excel-файл с ценами."
MSG_SELECT_MARK = "Выбери марку бетона:"
MSG_UNABLE_DETERMINE_MARK = "Не удалось определить выбранную марку."

MSG_ENTER_VOLUME = "Введи объем в м³."
MSG_BAD_VOLUME = "Введите корректный объем в м³. Например: 5 или 7.5"

MSG_ENTER_CONCRETE_DISCOUNT = "Введи скидку на бетон в %."
MSG_BAD_CONCRETE_DISCOUNT = "Введите скидку на бетон целым числом от 0 до 100."

MSG_ENTER_DISTANCE = "Введи расстояние в км."
MSG_BAD_DISTANCE = "Введите расстояние целым числом в км. Например: 25"
MSG_EMPTY_DISTANCE = "Список расстояний пуст. Проверь Excel-файл с ценами."
MSG_DISTANCE_LOAD_FAILED = "Не удалось загрузить прайс доставки. Проверь файл prices/prices.xlsx."
MSG_OUT_OF_RANGE = "Расстояние вне диапазона прайса."

MSG_ENTER_DELIVERY_DISCOUNT = "Введи скидку на доставку в %."
MSG_BAD_DELIVERY_DISCOUNT = "Введите скидку на доставку целым числом от 0 до 100."

MSG_ENTER_CLIENT_PRICE = "Введите стоимость бетона за 1 м³ для клиента:"
MSG_BAD_CLIENT_PRICE = "Введите корректную стоимость за 1 м³. Например: 3400"
MSG_CLIENT_PRICE_BELOW_COST = "⚠️ Введенная сумма ниже себестоимости"
MSG_CLIENT_PRICE_TOO_HIGH = "Нихрена себе, ты в себя поверил"
MSG_NO_ACTIVE_CALCULATION = "Нет активного расчёта"
MSG_NO_CLIENT_TEXT = "Сначала добавь маржу"

ADD_MARGIN_CALLBACK = "margin:add"
NEW_CALCULATION_CALLBACK = "margin:new"
BACK_TO_CALCULATION_CALLBACK = "margin:back_to_calculation"
BACK_TO_DELIVERY_DISCOUNT_CALLBACK = "margin:back_to_delivery_discount"
CLIENT_MESSAGE_CALLBACK = "margin:client_message"


class MarginCalculationStates(StatesGroup):
    waiting_for_client_price = State()


def format_total_money(value: float | int) -> str:
    return f"{int(round(float(value))):,}".replace(",", " ")


def format_unit_money(value: float | int) -> str:
    return str(int(round(float(value))))


def build_final_calculation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💵 Добавить маржу",
                    callback_data=ADD_MARGIN_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Изменить скидку доставки",
                    callback_data=BACK_TO_DELIVERY_DISCOUNT_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Новый расчёт",
                    callback_data=NEW_CALCULATION_CALLBACK,
                )
            ],
        ]
    )


def build_margin_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 SMS клиенту",
                    callback_data=CLIENT_MESSAGE_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к расчёту",
                    callback_data=BACK_TO_CALCULATION_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Новый расчёт",
                    callback_data=NEW_CALCULATION_CALLBACK,
                )
            ],
        ]
    )


def build_after_client_message_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад к расчёту",
                    callback_data=BACK_TO_CALCULATION_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Новый расчёт",
                    callback_data=NEW_CALCULATION_CALLBACK,
                )
            ],
        ]
    )


async def send_calculation_start_message(message: Message) -> None:
    try:
        items = load_concrete_prices()
    except Exception:
        await message.answer(MSG_PRICE_LOAD_FAILED)
        return

    if not items:
        await message.answer(MSG_EMPTY_CONCRETE)
        return

    await message.answer(MSG_SELECT_MARK, reply_markup=build_concrete_keyboard(items))


async def send_calculation_start_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    try:
        items = load_concrete_prices()
    except Exception:
        if callback.message:
            await callback.message.answer(MSG_PRICE_LOAD_FAILED)
        return

    if not items:
        if callback.message:
            await callback.message.answer(MSG_EMPTY_CONCRETE)
        return

    if callback.message:
        await callback.message.answer(
            MSG_SELECT_MARK,
            reply_markup=build_concrete_keyboard(items),
        )


@router.message(F.text == NEW_CALCULATION_TEXT)
async def handle_new_calculation(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_calculation_start_message(message)


@router.callback_query(F.data == NEW_CALCULATION_CALLBACK)
async def handle_new_calculation_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await send_calculation_start_callback(callback, state)


@router.callback_query(F.data.startswith("concrete:"))
async def handle_concrete_selection(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        items = load_concrete_prices()
        index = int((callback.data or "").split(":", 1)[1])
        item = items[index]
    except Exception:
        await callback.answer()
        if callback.message:
            await callback.message.answer(MSG_UNABLE_DETERMINE_MARK)
        return

    await state.update_data(
        concrete_index=index,
        concrete_full_label=item.full_label,
        concrete_short_label=item.short_label,
        concrete_price_uah_per_m3=item.price_uah_per_m3,
    )
    await state.set_state(ConcreteCalculationStates.waiting_for_volume)
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            f"Выбрана марка: {item.short_label}\n"
            f"Цена за 1 м³: {item.price_uah_per_m3} грн/м³\n\n"
            f"{MSG_ENTER_VOLUME}",
            reply_markup=build_back_keyboard("concrete"),
        )


@router.callback_query(F.data == "back:concrete")
async def handle_back_concrete(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    try:
        items = load_concrete_prices()
    except Exception:
        if callback.message:
            await callback.message.answer(MSG_PRICE_LOAD_FAILED)
        return

    if not items:
        if callback.message:
            await callback.message.answer(MSG_EMPTY_CONCRETE)
        return

    if callback.message:
        await callback.message.answer(
            MSG_SELECT_MARK,
            reply_markup=build_concrete_keyboard(items),
        )


@router.message(ConcreteCalculationStates.waiting_for_volume)
async def handle_volume_input(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip().replace(",", ".")

    try:
        volume = float(raw_value)
    except ValueError:
        await message.answer(MSG_BAD_VOLUME)
        return

    if volume <= 0:
        await message.answer(MSG_BAD_VOLUME)
        return

    await state.update_data(volume_m3=volume)
    await state.set_state(ConcreteCalculationStates.waiting_for_concrete_discount)

    await message.answer(
        f"Объем: {volume:g} м³\n\n{MSG_ENTER_CONCRETE_DISCOUNT}",
        reply_markup=build_back_keyboard("volume"),
    )


@router.callback_query(F.data == "back:volume")
async def handle_back_volume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    data = await state.get_data()
    concrete_short_label = data.get("concrete_short_label")
    concrete_price = data.get("concrete_price_uah_per_m3")

    await state.set_state(ConcreteCalculationStates.waiting_for_volume)

    if callback.message:
        await callback.message.answer(
            f"Выбрана марка: {concrete_short_label}\n"
            f"Цена за 1 м³: {concrete_price} грн/м³\n\n"
            f"{MSG_ENTER_VOLUME}",
            reply_markup=build_back_keyboard("concrete"),
        )


@router.message(ConcreteCalculationStates.waiting_for_concrete_discount)
async def handle_concrete_discount_input(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if not raw_value.isdigit():
        await message.answer(MSG_BAD_CONCRETE_DISCOUNT)
        return

    discount = int(raw_value)

    if discount < 0 or discount > 100:
        await message.answer(MSG_BAD_CONCRETE_DISCOUNT)
        return

    data = await state.get_data()
    price = int(data["concrete_price_uah_per_m3"])
    price_with_discount = int(round(price * (100 - discount) / 100))

    await state.update_data(
        concrete_discount_percent=discount,
        concrete_price_with_discount_uah_per_m3=price_with_discount,
    )
    await state.set_state(ConcreteCalculationStates.waiting_for_distance)

    await message.answer(
        f"Скидка на бетон: {discount}%\n"
        f"Цена бетона со скидкой: {price_with_discount} грн/м³\n\n"
        f"{MSG_ENTER_DISTANCE}",
        reply_markup=build_back_keyboard("concrete_discount"),
    )


@router.callback_query(F.data == "back:concrete_discount")
async def handle_back_concrete_discount(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    data = await state.get_data()
    volume = data.get("volume_m3")

    await state.set_state(ConcreteCalculationStates.waiting_for_concrete_discount)

    if callback.message:
        await callback.message.answer(
            f"Объем: {volume:g} м³\n\n{MSG_ENTER_CONCRETE_DISCOUNT}",
            reply_markup=build_back_keyboard("volume"),
        )


@router.message(ConcreteCalculationStates.waiting_for_distance)
async def handle_distance_input(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if not raw_value.isdigit():
        await message.answer(MSG_BAD_DISTANCE)
        return

    distance = int(raw_value)

    if distance <= 0:
        await message.answer(MSG_BAD_DISTANCE)
        return

    try:
        items = load_delivery_prices()
    except Exception:
        await message.answer(MSG_DISTANCE_LOAD_FAILED)
        return

    if not items:
        await message.answer(MSG_EMPTY_DISTANCE)
        return

    min_distance = items[0].distance_km
    max_distance = items[-1].distance_km

    if distance > max_distance:
        await message.answer(MSG_OUT_OF_RANGE)
        return

    if distance <= min_distance:
        matched_item = items[0]
    else:
        matched_item = None

        for item in items:
            if item.distance_km >= distance:
                matched_item = item
                break

        if matched_item is None:
            await message.answer(MSG_OUT_OF_RANGE)
            return

    await state.update_data(
        distance_km=distance,
        matched_delivery_distance_km=matched_item.distance_km,
        delivery_price_uah_per_m3=matched_item.price_per_cube,
    )
    await state.set_state(ConcreteCalculationStates.waiting_for_delivery_discount)

    await message.answer(
        f"Расстояние: {distance} км\n"
        f"Тариф доставки: {matched_item.distance_km} км\n"
        f"Цена доставки: {matched_item.price_per_cube} грн/м³\n\n"
        f"{MSG_ENTER_DELIVERY_DISCOUNT}",
        reply_markup=build_back_keyboard("distance"),
    )


@router.callback_query(F.data == "back:distance")
async def handle_back_distance(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    data = await state.get_data()
    concrete_discount_percent = data.get("concrete_discount_percent")
    concrete_price_with_discount = data.get("concrete_price_with_discount_uah_per_m3")

    await state.set_state(ConcreteCalculationStates.waiting_for_distance)

    if callback.message:
        await callback.message.answer(
            f"Скидка на бетон: {concrete_discount_percent}%\n"
            f"Цена бетона со скидкой: {concrete_price_with_discount} грн/м³\n\n"
            f"{MSG_ENTER_DISTANCE}",
            reply_markup=build_back_keyboard("concrete_discount"),
        )


@router.message(ConcreteCalculationStates.waiting_for_delivery_discount)
async def handle_delivery_discount_input(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()

    if not raw_value.isdigit():
        await message.answer(MSG_BAD_DELIVERY_DISCOUNT)
        return

    discount = int(raw_value)

    if discount < 0 or discount > 100:
        await message.answer(MSG_BAD_DELIVERY_DISCOUNT)
        return

    data = await state.get_data()

    delivery_price = int(data["delivery_price_uah_per_m3"])
    delivery_price_with_discount = int(round(delivery_price * (100 - discount) / 100))

    volume = float(data["volume_m3"])
    concrete_short_label = data["concrete_short_label"]
    concrete_price_with_discount = float(data["concrete_price_with_discount_uah_per_m3"])
    concrete_discount_percent = int(data["concrete_discount_percent"])
    distance_km = int(data["distance_km"])

    truck_count = 1 if volume <= 11 else ceil(volume / 11)

    volume_rounded = round(volume, 1)
    whole_volume = int(volume_rounded)
    decimal_part = round(volume_rounded - whole_volume, 1)

    if truck_count == 1:
        truck_parts = [volume_rounded]
    else:
        base = whole_volume // truck_count
        remainder = whole_volume % truck_count

        truck_parts = [
            base + 1 if index < remainder else base
            for index in range(truck_count)
        ]

        if decimal_part > 0:
            truck_parts[-1] = round(truck_parts[-1] + decimal_part, 1)

    truck_parts.sort(reverse=True)
    truck_split_text = " + ".join(f"{part:g}" for part in truck_parts)

    delivery_billable_volume_m3 = sum(part if part >= 7 else 7 for part in truck_parts)
    concrete_total = volume * concrete_price_with_discount
    delivery_total = delivery_billable_volume_m3 * delivery_price_with_discount
    total_cost = concrete_total + delivery_total
    cost_per_m3 = round(total_cost / volume)

    text = (
        f"✅ Расчёт готов\n\n"

        f"🏭 Бетон\n"
        f"Марка: {concrete_short_label}\n"
        f"Объем: {volume:g} м³\n"
        f"Расстояние: {distance_km} км\n\n"

        f"💸 Скидки: бетон -{concrete_discount_percent}%, доставка -{discount}%\n\n"

        f"🚚 Доставка\n"
        f"Машин: {truck_count}\n"
        f"Разбивка: {truck_split_text}\n\n"

        f"💰 Итого\n"
        f"Общая стоимость: {format_total_money(total_cost)} грн\n"
        f"Стоимость 1 м³: {format_unit_money(cost_per_m3)} грн"
    )

    await state.update_data(
        delivery_discount_percent=discount,
        delivery_price_with_discount_uah_per_m3=delivery_price_with_discount,
        delivery_billable_volume_m3=delivery_billable_volume_m3,
        truck_count=truck_count,
        truck_split_text=truck_split_text,
        total_cost_uah=total_cost,
        cost_per_m3_uah=cost_per_m3,
        last_calculation_text=text,
    )

    data = await state.get_data()
    await state.set_state(None)

    await message.answer(
        text=text,
        reply_markup=build_final_calculation_keyboard(),
    )

    asyncio.create_task(
        asyncio.to_thread(
            save_to_google_sheets,
            {
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "phone": data.get("phone"),
                "concrete_mark": data.get("concrete_short_label"),
                "amount": data.get("volume_m3"),
                "concrete_discount": data.get("concrete_discount_percent"),
                "distance": data.get("distance_km"),
                "distance_discount": data.get("delivery_discount_percent"),
                "total_cost": total_cost,
                "price_per_m3": cost_per_m3,
            },
        )
    )


@router.callback_query(F.data == ADD_MARGIN_CALLBACK)
async def handle_add_margin(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    if not data.get("last_calculation_text") or not data.get("cost_per_m3_uah"):
        await callback.answer(MSG_NO_ACTIVE_CALCULATION, show_alert=True)
        return

    await state.set_state(MarginCalculationStates.waiting_for_client_price)
    await callback.answer()

    if callback.message:
        await callback.message.answer(MSG_ENTER_CLIENT_PRICE)


@router.message(MarginCalculationStates.waiting_for_client_price)
async def handle_client_price_input(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip().replace(" ", "").replace(",", ".")

    try:
        client_price_per_m3 = float(raw_value)
    except ValueError:
        await message.answer(MSG_BAD_CLIENT_PRICE)
        return

    data = await state.get_data()

    cost_per_m3 = float(data["cost_per_m3_uah"])
    volume = float(data["volume_m3"])
    total_cost = float(data["total_cost_uah"])
    concrete_short_label = data["concrete_short_label"]
    last_calculation_text = data.get("last_calculation_text")

    if client_price_per_m3 < cost_per_m3:
        await message.answer(MSG_CLIENT_PRICE_BELOW_COST)
        return

    if client_price_per_m3 > 7500:
        await message.answer(MSG_CLIENT_PRICE_TOO_HIGH)
        return

    client_total = client_price_per_m3 * volume
    margin_per_m3 = client_price_per_m3 - cost_per_m3
    margin_total = client_total - total_cost

    client_message_text = (
        f"Бетон {concrete_short_label} {volume:g} м³ по "
        f"{format_unit_money(client_price_per_m3)} грн/м³\n"
        f"Загальна сума з  доставкою: {format_total_money(client_total)} грн"
    )

    text = (
        f"{last_calculation_text}\n\n"

        f"👤 Для клиента\n"
        f"Цена 1 м³ для клиента: {format_unit_money(client_price_per_m3)} грн\n"
        f"Общая стоимость для клиента: {format_total_money(client_total)} грн\n\n"

        f"💼 Маржа\n"
        f"Маржа с 1 м³: {format_unit_money(margin_per_m3)} грн\n"
        f"Маржа общая: {format_total_money(margin_total)} грн"
    )

    await state.update_data(
        client_price_per_m3_uah=client_price_per_m3,
        client_total_uah=client_total,
        margin_per_m3_uah=margin_per_m3,
        margin_total_uah=margin_total,
        client_message_text=client_message_text,
        last_margin_text=text,
    )
    await state.set_state(None)

    await message.answer(
        text=text,
        reply_markup=build_margin_result_keyboard(),
    )

    asyncio.create_task(
        asyncio.to_thread(
            update_margin_in_google_sheets,
            {
                "user_id": message.from_user.id,
                "total_cost": total_cost,
                "price_per_m3": cost_per_m3,
                "client_price": client_price_per_m3,
                "client_total": client_total,
                "margin_total": margin_total,
            },
        )
    )


@router.callback_query(F.data == CLIENT_MESSAGE_CALLBACK)
async def handle_client_message(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    client_message_text = data.get("client_message_text")

    await callback.answer()

    if not client_message_text:
        if callback.message:
            await callback.message.answer(MSG_NO_CLIENT_TEXT)
        return

    if callback.message:
        await callback.message.answer(
            text=client_message_text,
            reply_markup=build_after_client_message_keyboard(),
        )


@router.callback_query(F.data == BACK_TO_CALCULATION_CALLBACK)
async def handle_back_to_calculation(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get("last_calculation_text")

    await state.set_state(None)
    await callback.answer()

    if not text:
        if callback.message:
            await callback.message.answer(MSG_NO_ACTIVE_CALCULATION)
        return

    if callback.message:
        await callback.message.answer(
            text=text,
            reply_markup=build_final_calculation_keyboard(),
        )


@router.callback_query(F.data == BACK_TO_DELIVERY_DISCOUNT_CALLBACK)
async def handle_back_to_delivery_discount(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    required_fields = [
        "distance_km",
        "matched_delivery_distance_km",
        "delivery_price_uah_per_m3",
    ]

    if any(data.get(field) is None for field in required_fields):
        await callback.answer(MSG_NO_ACTIVE_CALCULATION, show_alert=True)
        return

    distance_km = int(data["distance_km"])
    matched_delivery_distance_km = int(data["matched_delivery_distance_km"])
    delivery_price = int(data["delivery_price_uah_per_m3"])

    await state.set_state(ConcreteCalculationStates.waiting_for_delivery_discount)
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            f"Расстояние: {distance_km} км\n"
            f"Тариф доставки: {matched_delivery_distance_km} км\n"
            f"Цена доставки: {delivery_price} грн/м³\n\n"
            f"{MSG_ENTER_DELIVERY_DISCOUNT}",
            reply_markup=build_back_keyboard("distance"),
        )