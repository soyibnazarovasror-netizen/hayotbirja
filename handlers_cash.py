from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from i18n import t
from states import CashStates

router = Router()


async def show_cash_menu(target, lang: str, edit: bool = True):
    cash = await db.get_cash()
    text = t(lang, "cash_title", usd=cash["USD"], uzs=cash["UZS"])
    markup = kb.cash_menu_kb(lang)
    if edit:
        await target.message.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.callback_query(F.data == "menu:cash")
async def open_cash_menu(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.clear()
    await show_cash_menu(call, lang)
    await call.answer()


@router.callback_query(F.data == "back:cash")
async def back_to_cash(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.clear()
    await show_cash_menu(call, lang)
    await call.answer()


@router.callback_query(F.data == "cash:add")
async def cash_add_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.update_data(action="add", reason="manual")
    await state.set_state(CashStates.choosing_currency)
    await call.message.edit_text(t(lang, "choose_currency"), reply_markup=kb.currency_kb(lang, "currency"))
    await call.answer()


@router.callback_query(F.data == "cash:withdraw")
async def cash_withdraw_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.update_data(action="withdraw")
    await state.set_state(CashStates.choosing_currency)
    await call.message.edit_text(t(lang, "choose_currency"), reply_markup=kb.currency_kb(lang, "currency"))
    await call.answer()


@router.callback_query(CashStates.choosing_currency, F.data.startswith("currency:"))
async def cash_currency_chosen(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    currency = call.data.split(":")[1]
    await state.update_data(currency=currency)
    await state.set_state(CashStates.entering_amount)
    await call.message.edit_text(t(lang, "enter_amount"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(CashStates.entering_amount)
async def cash_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return
    await state.update_data(amount=amount)
    await state.set_state(CashStates.entering_comment)
    data = await state.get_data()
    prompt_key = "enter_income_source" if data["action"] == "add" else "enter_expense_purpose"
    await message.answer(t(lang, prompt_key), reply_markup=kb.skip_comment_kb(lang))


@router.callback_query(CashStates.entering_comment, F.data == "skip_comment")
async def cash_comment_skipped(call: CallbackQuery, state: FSMContext):
    await finalize_cash_operation(call.message, state, call.from_user.id, comment="-")
    await call.answer()


@router.message(CashStates.entering_comment)
async def cash_comment_entered(message: Message, state: FSMContext):
    comment = message.text.strip()
    await finalize_cash_operation(message, state, message.from_user.id, comment=comment)


async def finalize_cash_operation(message_target, state: FSMContext, user_id: int, comment: str):
    lang = await db.get_user_lang(user_id)
    data = await state.get_data()
    action = data["action"]
    currency = data["currency"]
    amount = data["amount"]

    if action == "add":
        await db.adjust_cash(currency, amount)
        note = f"+{amount} {currency} — {comment}"
        await db.add_history("cash_add", note)
        text = t(lang, "cash_added", amount=amount, currency=currency)
    else:
        await db.adjust_cash(currency, -amount)
        note = f"-{amount} {currency} — {comment}"
        await db.add_history("cash_withdraw", note)
        text = t(lang, "cash_withdrawn", amount=amount, currency=currency)

    await state.clear()
    if isinstance(message_target, Message):
        await message_target.answer(text, reply_markup=kb.back_kb(lang, "cash"))
    else:
        await message_target.edit_text(text, reply_markup=kb.back_kb(lang, "cash"))


# ---------- Exchange ----------

@router.callback_query(F.data == "cash:exchange")
async def exchange_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.set_state(CashStates.exchange_from_currency)
    await call.message.edit_text(t(lang, "exchange_from"), reply_markup=kb.currency_kb(lang, "excurrency"))
    await call.answer()


@router.callback_query(CashStates.exchange_from_currency, F.data.startswith("excurrency:"))
async def exchange_currency_chosen(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    from_cur = call.data.split(":")[1]
    to_cur = "UZS" if from_cur == "USD" else "USD"
    await state.update_data(from_cur=from_cur, to_cur=to_cur)
    await state.set_state(CashStates.exchange_amount)
    await call.message.edit_text(t(lang, "enter_amount"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(CashStates.exchange_amount)
async def exchange_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return
    await state.update_data(amount=amount)
    await state.set_state(CashStates.exchange_rate)
    await message.answer(t(lang, "exchange_rate"), reply_markup=kb.cancel_kb(lang))


@router.message(CashStates.exchange_rate)
async def exchange_rate_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        rate = float(message.text.replace(",", ".").strip())
        if rate <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return

    data = await state.get_data()
    from_cur, to_cur, amount = data["from_cur"], data["to_cur"], data["amount"]

    if from_cur == "USD":
        to_amount = amount * rate
    else:
        to_amount = amount / rate

    await db.adjust_cash(from_cur, -amount)
    await db.adjust_cash(to_cur, to_amount)
    await db.add_history(
        "exchange",
        f"Обмен: {amount} {from_cur} -> {to_amount:.2f} {to_cur} (курс {rate})",
    )

    text = t(lang, "exchange_done", from_amt=amount, from_cur=from_cur, to_amt=to_amount, to_cur=to_cur, rate=rate)
    await state.clear()
    await message.answer(text, reply_markup=kb.back_kb(lang, "cash"))


# ---------- Lot movements ----------

@router.callback_query(F.data == "cash:lotmovements")
async def cash_lot_movements(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    lots = await db.get_lots_cash_movements()
    if not lots:
        await call.message.edit_text(t(lang, "no_lots"), reply_markup=kb.back_kb(lang, "cash"))
        await call.answer()
        return

    lines = []
    for lot in lots:
        expenses_str = ", ".join(f"{amt:.0f} {cur}" for cur, amt in lot["expenses"].items()) or "0"
        if lot["status"] == "closed" and lot["received_amount"] is not None:
            currency = lot["received_currency"]
            spent_in_currency = lot["expenses"].get(currency, 0)
            profit = lot["received_amount"] - spent_in_currency
            lines.append(t(
                lang, "lot_movement_item_closed",
                name=lot["name"], received=f"{lot['received_amount']:.0f} {currency}",
                expenses=expenses_str, profit=profit, currency=currency,
            ))
        else:
            lines.append(t(lang, "lot_movement_item_open", name=lot["name"], expenses=expenses_str))

    text = t(lang, "lot_movements_title") + "\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=kb.back_kb(lang, "cash"))
    await call.answer()


# ---------- Cash operations history ----------

@router.callback_query(F.data == "cash:history")
async def cash_history_list(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    records = await db.get_cash_history(limit=30)
    if not records:
        await call.message.edit_text(t(lang, "no_history"), reply_markup=kb.back_kb(lang, "cash"))
        await call.answer()
        return

    lines = []
    for r in records:
        icon = "🟢" if r["type"] == "cash_add" else "🔴"
        lines.append(f"{icon} {r['date'].strftime('%d.%m %H:%M')} — {r['text']}")
    text = t(lang, "cash_history_title") + "\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=kb.back_kb(lang, "cash"))
    await call.answer()
