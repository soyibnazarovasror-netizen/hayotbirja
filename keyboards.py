from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from i18n import t


def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "menu_cash"), callback_data="menu:cash")
    b.button(text=t(lang, "menu_loans"), callback_data="menu:loans")
    b.button(text=t(lang, "menu_lots"), callback_data="menu:lots")
    b.button(text=t(lang, "menu_reports"), callback_data="menu:reports")
    b.button(text=t(lang, "menu_history"), callback_data="menu:history")
    b.button(text=t(lang, "menu_lang"), callback_data="menu:lang")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def back_kb(lang: str, target: str = "main") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "back"), callback_data=f"back:{target}")
    return b.as_markup()


def cancel_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    return b.as_markup()


def lang_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    b.adjust(2)
    return b.as_markup()


# ---------- Cash ----------

def cash_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "cash_add"), callback_data="cash:add")
    b.button(text=t(lang, "cash_withdraw"), callback_data="cash:withdraw")
    b.button(text=t(lang, "cash_exchange"), callback_data="cash:exchange")
    b.button(text=t(lang, "cash_lot_movements"), callback_data="cash:lotmovements")
    b.button(text=t(lang, "cash_history_btn"), callback_data="cash:history")
    b.button(text=t(lang, "back"), callback_data="back:main")
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def currency_kb(lang: str, prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "currency_usd"), callback_data=f"{prefix}:USD")
    b.button(text=t(lang, "currency_uzs"), callback_data=f"{prefix}:UZS")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(2, 1)
    return b.as_markup()


def cash_add_reason_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "cash_reason_manual"), callback_data="cashreason:manual")
    b.button(text=t(lang, "cash_reason_lot_sale"), callback_data="cashreason:lot")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(1, 1, 1)
    return b.as_markup()


def skip_comment_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "skip"), callback_data="skip_comment")
    return b.as_markup()


# ---------- Loans ----------

def loans_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "loan_add"), callback_data="loan:add")
    b.button(text=t(lang, "loan_return"), callback_data="loan:return")
    b.button(text=t(lang, "loans_list"), callback_data="loan:list")
    b.button(text=t(lang, "loan_edit"), callback_data="loan:edit")
    b.button(text=t(lang, "loan_delete"), callback_data="loan:delete")
    b.button(text=t(lang, "back"), callback_data="back:main")
    b.adjust(2, 1, 2, 1)
    return b.as_markup()


def loans_select_for_action_kb(lang: str, loans: list, prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for loan in loans:
        label = f"{loan['creditor_name']}: {loan['amount']:.0f} {loan['currency']} ({loan['created_at'].strftime('%d.%m.%y')})"
        b.button(text=label, callback_data=f"{prefix}:{loan['_id']}")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(1)
    return b.as_markup()


def confirm_kb(lang: str, yes_cb: str, no_cb: str = "cancel") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "confirm_yes"), callback_data=yes_cb)
    b.button(text=t(lang, "confirm_no"), callback_data=no_cb)
    b.adjust(2)
    return b.as_markup()


def creditors_kb(lang: str, creditors: list, callback_prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for name in creditors:
        b.button(text=name, callback_data=f"{callback_prefix}:{name}")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(1)
    return b.as_markup()


def loans_select_kb(lang: str, loans: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for loan in loans:
        label = f"{loan['remaining']:.0f} {loan['currency']} ({loan['created_at'].strftime('%d.%m.%y')})"
        b.button(text=label, callback_data=f"selectloan:{loan['_id']}")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(1)
    return b.as_markup()


# ---------- Lots ----------

def lots_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "lot_add"), callback_data="lot:add")
    b.button(text=t(lang, "lot_list_open"), callback_data="lot:list_open")
    b.button(text=t(lang, "lot_list_closed"), callback_data="lot:list_closed")
    b.button(text=t(lang, "back"), callback_data="back:main")
    b.adjust(1, 1, 1, 1)
    return b.as_markup()


def lots_list_kb(lang: str, lots: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    status_icons = {"open": "🟡", "in_progress": "🔵", "closed": "✅"}
    for lot in lots:
        icon = status_icons.get(lot["status"], "")
        b.button(text=f"{icon} {lot['name']}", callback_data=f"viewlot:{lot['_id']}")
    b.button(text=t(lang, "back"), callback_data="back:lots")
    b.adjust(1)
    return b.as_markup()


def lot_detail_kb(lang: str, lot_id: str, status: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "lot_add_expense"), callback_data=f"lotaction:expense:{lot_id}")
    b.button(text=t(lang, "lot_view_expenses"), callback_data=f"lotaction:viewexp:{lot_id}")
    if status != "closed":
        b.button(text=t(lang, "lot_change_status"), callback_data=f"lotaction:status:{lot_id}")
        b.button(text=t(lang, "lot_close"), callback_data=f"lotaction:close:{lot_id}")
        b.button(text=t(lang, "lot_edit_agreed"), callback_data=f"lotaction:editagreed:{lot_id}")
    else:
        b.button(text=t(lang, "lot_edit_received"), callback_data=f"lotaction:editreceived:{lot_id}")
    b.button(text=t(lang, "lot_delete"), callback_data=f"lotaction:delete:{lot_id}")
    b.button(text=t(lang, "back"), callback_data="back:lots")
    b.adjust(1)
    return b.as_markup()


def expenses_list_kb(lang: str, lot_id: str, expenses: list, cat_labels: dict) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for e in expenses:
        label = f"{cat_labels.get(e['category'], e['category'])}: {e['amount']:.0f} {e['currency']}"
        b.button(text=label, callback_data=f"expsel:{lot_id}:{e['id']}")
    b.button(text=t(lang, "back"), callback_data=f"viewlot:{lot_id}")
    b.adjust(1)
    return b.as_markup()


def expense_action_kb(lang: str, lot_id: str, expense_id: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "expense_edit_amount_btn"), callback_data=f"expedit:{lot_id}:{expense_id}")
    b.button(text=t(lang, "expense_delete_btn"), callback_data=f"expdel:{lot_id}:{expense_id}")
    b.button(text=t(lang, "cancel"), callback_data=f"viewlot:{lot_id}")
    b.adjust(1)
    return b.as_markup()


def expense_category_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "cat_purchase"), callback_data="expcat:purchase")
    b.button(text=t(lang, "cat_tax"), callback_data="expcat:tax")
    b.button(text=t(lang, "cat_taxi"), callback_data="expcat:taxi")
    b.button(text=t(lang, "cat_delivery"), callback_data="expcat:delivery")
    b.button(text=t(lang, "cat_other"), callback_data="expcat:other")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def lot_status_kb(lang: str, lot_id: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "status_open"), callback_data=f"setstatus:{lot_id}:open")
    b.button(text=t(lang, "status_in_progress"), callback_data=f"setstatus:{lot_id}:in_progress")
    b.button(text=t(lang, "cancel"), callback_data="cancel")
    b.adjust(1, 1, 1)
    return b.as_markup()


# ---------- Reports ----------

def reports_menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "report_summary"), callback_data="report:summary")
    b.button(text=t(lang, "report_lots_profit"), callback_data="report:lots_profit")
    b.button(text=t(lang, "back"), callback_data="back:main")
    b.adjust(1, 1, 1)
    return b.as_markup()
