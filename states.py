from aiogram.fsm.state import State, StatesGroup


class CashStates(StatesGroup):
    choosing_action = State()
    choosing_currency = State()
    entering_amount = State()
    entering_comment = State()
    choosing_add_reason = State()
    choosing_lot_for_income = State()

    exchange_from_currency = State()
    exchange_amount = State()
    exchange_rate = State()


class LoanStates(StatesGroup):
    entering_creditor_name = State()
    choosing_currency = State()
    entering_amount = State()

    choosing_creditor_for_return = State()
    choosing_loan_for_return = State()
    entering_return_amount = State()


class LotStates(StatesGroup):
    entering_name = State()
    choosing_currency = State()
    entering_purchase_amount = State()

    viewing_lot = State()
    choosing_expense_category = State()
    entering_expense_currency = State()
    entering_expense_amount = State()
    entering_expense_comment = State()

    choosing_new_status = State()

    entering_sale_currency = State()
    entering_sale_amount = State()
    