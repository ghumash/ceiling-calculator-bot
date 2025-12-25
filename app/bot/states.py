"""FSM состояния для диалога расчёта."""

from aiogram.fsm.state import State, StatesGroup


class CalculationStates(StatesGroup):
    """FSM состояния для процесса расчёта."""

    # Базовая информация
    waiting_for_area = State()
    waiting_for_corners = State()
    waiting_for_perimeter = State()

    # Выбор материалов
    choosing_fabric = State()
    choosing_profile = State()

    # Карнизы
    asking_cornices = State()
    choosing_cornice = State()
    entering_cornice_length = State()

    # Освещение
    entering_spotlights = State()
    asking_ceramic = State()
    entering_ceramic_area = State()
    entering_chandeliers = State()

    # Готовность к расчёту
    ready_to_calculate = State()

    # Результат
    showing_result = State()
