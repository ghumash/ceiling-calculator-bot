"""FSM состояния для диалога расчёта."""

from aiogram.fsm.state import State, StatesGroup


class CalculationStates(StatesGroup):
    """FSM состояния для процесса расчёта."""

    # Выбор способа связи
    choosing_contact_method = State()

    # Базовая информация
    waiting_for_area = State()

    # Выбор профиля
    choosing_profile = State()

    # Карнизы
    entering_cornice_length = State()
    choosing_cornice_type = State()

    # Освещение
    entering_spotlights = State()
    entering_chandeliers = State()

    # Результат
    showing_result = State()

    # Заказ замера
    entering_name = State()
    entering_phone = State()
    entering_address = State()

    # Режим редактирования
    editing_menu = State()
    editing_area = State()
    editing_profile = State()
    editing_cornice_length = State()
    editing_cornice_type = State()
    editing_spotlights = State()
    editing_chandeliers = State()
