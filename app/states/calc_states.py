from aiogram.fsm.state import State, StatesGroup


class ConcreteCalculationStates(StatesGroup):
    waiting_for_volume = State()
    waiting_for_concrete_discount = State()
    waiting_for_distance = State()
    waiting_for_delivery_discount = State()