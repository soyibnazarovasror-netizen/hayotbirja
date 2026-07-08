from aiogram import Router, F
from aiogram.types import CallbackQuery

import db
import keyboards as kb
from i18n import t

router = Router()

HISTORY_ICONS = {
    "loan_in": "🤝➕", "loan_return": "🤝➖", "lot_create": "📦",
    "lot_expense": "📉", "lot_close": "🎉", "cash_add": "💰➕",
    "cash_withdraw": "💰➖", "exchange": "🔄",
}


@router.callback_query(F.data == "menu:reports")
async def open_reports_menu(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    await call.message.edit_text(t(lang, "reports_title"), reply_markup=kb.reports_menu_kb(lang))
    await call.answer()


@router.callback_query(F.data == "back:reports")
async def back_to_reports(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    await call.message.edit_text(t(lang, "reports_title"), reply_markup=kb.reports_menu_kb(lang))
    await call.answer()


@router.callback_query(F.data == "report:summary")
async def report_summary(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    cash = await db.get_cash()
    debt = await db.get_total_debt()
    lots_count = await db.count_lots_by_status()
    profit = await db.get_lots_profit_summary()

    text = t(
        lang, "report_summary_text",
        cash_usd=cash["USD"], cash_uzs=cash["UZS"],
        debt_usd=debt["USD"], debt_uzs=debt["UZS"],
        open_lots=lots_count["open"], closed_lots=lots_count["closed"],
        profit_usd=profit["USD"], profit_uzs=profit["UZS"],
    )
    await call.message.edit_text(text, reply_markup=kb.back_kb(lang, "reports"))
    await call.answer()


@router.callback_query(F.data == "report:lots_profit")
async def report_lots_profit(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    lots = await db.list_lots(status="closed")
    if not lots:
        await call.message.edit_text(t(lang, "no_closed_lots"), reply_markup=kb.back_kb(lang, "reports"))
        await call.answer()
        return

    lines = []
    for lot in lots:
        icon = "📈" if lot["profit"] >= 0 else "📉"
        lines.append(f"{icon} {lot['name']}: {lot['profit']:.2f} {lot['received_currency']}")
    text = t(lang, "report_lots_profit") + "\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=kb.back_kb(lang, "reports"))
    await call.answer()


@router.callback_query(F.data == "menu:history")
async def open_history(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    records = await db.get_recent_history(limit=15)
    if not records:
        await call.message.edit_text(t(lang, "no_history"), reply_markup=kb.back_kb(lang, "main"))
        await call.answer()
        return

    lines = []
    for r in records:
        icon = HISTORY_ICONS.get(r["type"], "•")
        lines.append(t(lang, "history_item", icon=icon, date=r["date"].strftime("%d.%m %H:%M"), text=r["text"]))
    text = t(lang, "history_title") + "\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=kb.back_kb(lang, "main"))
    await call.answer()
