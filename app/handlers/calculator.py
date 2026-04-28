import asyncio
from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.calculator import (
    build_back_keyboard,
    build_concrete_keyboard,
    build_main_menu_keyboard,
)
from app.services.price_loader import load_concrete_prices, load_delivery_prices
from app.services.google_sheets import save_to_google_sheets
from app.states.calc_states import ConcreteCalculationStates


router = Router()

NEW_CALCULATION_TEXT = "\u041d\u043e\u0432\u044b\u0439 \u0440\u0430\u0441\u0447\u0435\u0442"
NEW_CALCULATION_BUTTON = "\u041d\u043e\u0432\u044b\u0439 \u0440\u0430\u0441\u0447\u0435\u0442"
MSG_PRICE_LOAD_FAILED = "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u043f\u0440\u0430\u0439\u0441. \u041f\u0440\u043e\u0432\u0435\u0440\u044c \u0444\u0430\u0439\u043b prices/prices.xlsx."
MSG_EMPTY_CONCRETE = "\u0421\u043f\u0438\u0441\u043e\u043a \u043c\u0430\u0440\u043e\u043a \u043f\u0443\u0441\u0442. \u041f\u0440\u043e\u0432\u0435\u0440\u044c Excel-\u0444\u0430\u0439\u043b \u0441 \u0446\u0435\u043d\u0430\u043c\u0438."
MSG_SELECT_MARK = "\u0412\u044b\u0431\u0435\u0440\u0438 \u043c\u0430\u0440\u043a\u0443 \u0431\u0435\u0442\u043e\u043d\u0430:"
MSG_UNABLE_DETERMINE_MARK = "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u0443\u044e \u043c\u0430\u0440\u043a\u0443."
MSG_ENTER_VOLUME = "\u0412\u0432\u0435\u0434\u0438 \u043e\u0431\u044a\u0435\u043c \u0432 \u043c\u00b3."
MSG_BAD_VOLUME = "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u044b\u0439 \u043e\u0431\u044a\u0435\u043c \u0432 \u043c\u00b3. \u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: 5 \u0438\u043b\u0438 7.5"
MSG_ENTER_CONCRETE_DISCOUNT = "\u0412\u0432\u0435\u0434\u0438 \u0441\u043a\u0438\u0434\u043a\u0443 \u043d\u0430 \u0431\u0435\u0442\u043e\u043d \u0432 %."
MSG_BAD_CONCRETE_DISCOUNT = "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043a\u0438\u0434\u043a\u0443 \u043d\u0430 \u0431\u0435\u0442\u043e\u043d \u0446\u0435\u043b\u044b\u043c \u0447\u0438\u0441\u043b\u043e\u043c \u043e\u0442 0 \u0434\u043e 100."
MSG_ENTER_DISTANCE = "\u0412\u0432\u0435\u0434\u0438 \u0440\u0430\u0441\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u0432 \u043a\u043c."
MSG_BAD_DISTANCE = "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0440\u0430\u0441\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u0446\u0435\u043b\u044b\u043c \u0447\u0438\u0441\u043b\u043e\u043c \u0432 \u043a\u043c. \u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: 25"
MSG_EMPTY_DISTANCE = "\u0421\u043f\u0438\u0441\u043e\u043a \u0440\u0430\u0441\u0441\u0442\u043e\u044f\u043d\u0438\u0439 \u043f\u0443\u0441\u0442. \u041f\u0440\u043e\u0432\u0435\u0440\u044c Excel-\u0444\u0430\u0439\u043b \u0441 \u0446\u0435\u043d\u0430\u043c\u0438."
MSG_DISTANCE_LOAD_FAILED = "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u043f\u0440\u0430\u0439\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438. \u041f\u0440\u043e\u0432\u0435\u0440\u044c \u0444\u0430\u0439\u043b prices/prices.xlsx."
MSG_OUT_OF_RANGE = "\u0420\u0430\u0441\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u0432\u043d\u0435 \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d\u0430 \u043f\u0440\u0430\u0439\u0441\u0430."
MSG_ENTER_DELIVERY_DISCOUNT = "\u0412\u0432\u0435\u0434\u0438 \u0441\u043a\u0438\u0434\u043a\u0443 \u043d\u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443 \u0432 %."
MSG_BAD_DELIVERY_DISCOUNT = "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043a\u0438\u0434\u043a\u0443 \u043d\u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443 \u0446\u0435\u043b\u044b\u043c \u0447\u0438\u0441\u043b\u043e\u043c \u043e\u0442 0 \u0434\u043e 100."


@router.message(F.text == NEW_CALCULATION_TEXT)
async def handle_new_calculation(message: Message, state: FSMContext) -> None:
    await state.clear()

    try:
        items = load_concrete_prices()
    except Exception:
        await message.answer(MSG_PRICE_LOAD_FAILED)
        return

    if not items:
        await message.answer(MSG_EMPTY_CONCRETE)
        return

    await message.answer(MSG_SELECT_MARK, reply_markup=build_concrete_keyboard(items))


@router.callback_query(F.data.startswith("concrete:"))
async def handle_concrete_selection(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        items = load_concrete_prices()
        index = int((callback.data or "").split(":", 1)[1])
        item = items[index]
    except (IndexError, ValueError, TypeError, Exception):
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
            f"Цена за 1 м³ : {item.price_uah_per_m3} грн/м³\n\n"
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
    matched_delivery_distance_km = int(data["matched_delivery_distance_km"])

    truck_count = 1 if volume <= 11 else ceil(volume / 11)

    volume_rounded = round(volume, 1)

    if truck_count == 1:
        truck_parts = [volume_rounded]
    else:
        base_part = round(volume_rounded / truck_count, 1)
        truck_parts = [base_part for _ in range(truck_count)]

        difference = round(volume_rounded - sum(truck_parts), 1)
        truck_parts[0] = round(truck_parts[0] + difference, 1)

        truck_parts.sort(reverse=True)

    truck_split_text = " + ".join(f"{part:g}" for part in truck_parts)

    truck_split_text = " + ".join(f"{part:g}" for part in truck_parts)
    delivery_billable_volume_m3 = sum(part if part >= 7 else 7 for part in truck_parts)
    concrete_total = volume * concrete_price_with_discount
    delivery_total = delivery_billable_volume_m3 * delivery_price_with_discount
    total_cost = concrete_total + delivery_total
    cost_per_m3 = round(total_cost / volume)

    await state.update_data(
        delivery_discount_percent=discount,
        delivery_price_with_discount_uah_per_m3=delivery_price_with_discount,
        delivery_billable_volume_m3=delivery_billable_volume_m3,
        truck_count=truck_count,
        truck_split_text=truck_split_text,
        total_cost_uah=total_cost,
        cost_per_m3_uah=cost_per_m3,
    )

    data = await state.get_data()

    await state.clear()

    text = (
        f"✅ Расчёт готов\n\n"

        f"🏭 Бетон\n"
        f"Марка: {concrete_short_label}\n"
        f"Объем: {volume:g} м³\n"
        f"Расстояние: {distance_km} км\n\n"
        f"💸 Скидки: бетон -{discount_percent}%, доставка -{delivery_discount_percent}%\n\n"

        f"🚚 Доставка\n"
        f"Машин: {truck_count}\n"
        f"Разбивка: {truck_split_text}\n\n"

        f"💰 Итого\n"
        f"Общая стоимость: {int(round(total_cost))} грн\n"
        f"Стоимость 1 м³: {int(round(cost_per_m3))} грн"
    )

    await message.answer(
        text=text,
        reply_markup=build_main_menu_keyboard(),
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