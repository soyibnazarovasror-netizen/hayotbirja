from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from i18n import t
from states import LoanStates

router = Router()


async def show_loans_menu(target, lang: str, edit: bool = True):
    debt = await db.get_total_debt()
    text = t(lang, "loans_title", usd=debt["USD"], uzs=debt["UZS"])
    markup = kb.loans_menu_kb(lang)
    if edit:
        await target.message.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.callback_query(F.data == "menu:loans")
async def open_loans_menu(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.clear()
    await show_loans_menu(call, lang)
    await call.answer()


@router.callback_query(F.data == "back:loans")
async def back_to_loans(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.clear()
    await show_loans_menu(call, lang)
    await call.answer()


# ---------- Add loan ----------

@router.callback_query(F.data == "loan:add")
async def loan_add_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.set_state(LoanStates.entering_creditor_name)
    await call.message.edit_text(t(lang, "enter_creditor_name"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(LoanStates.entering_creditor_name)
async def loan_creditor_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    name = message.text.strip()
    await state.update_data(creditor_name=name)
    await state.set_state(LoanStates.choosing_currency)
    await message.answer(t(lang, "choose_currency"), reply_markup=kb.currency_kb(lang, "loancurrency"))


@router.callback_query(LoanStates.choosing_currency, F.data.startswith("loancurrency:"))
async def loan_currency_chosen(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    currency = call.data.split(":")[1]
    await state.update_data(currency=currency)
    await state.set_state(LoanStates.entering_amount)
    await call.message.edit_text(t(lang, "enter_amount"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(LoanStates.entering_amount)
async def loan_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return

    data = await state.get_data()
    name = data["creditor_name"]
    currency = data["currency"]

    await db.create_loan(name, amount, currency)
    text = t(lang, "loan_added", name=name, amount=amount, currency=currency)
    await state.clear()
    await message.answer(text, reply_markup=kb.back_kb(lang, "loans"))


# ---------- List loans ----------

@router.callback_query(F.data == "loan:list")
async def loan_list(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    loans = await db.list_all_loans()
    if not loans:
        await call.message.edit_text(t(lang, "no_creditors"), reply_markup=kb.back_kb(lang, "loans"))
        await call.answer()
        return

    lines = []
    for loan in loans:
        icon = t(lang, "loan_status_done") if loan["status"] == "done" else t(lang, "loan_status_active")
        lines.append(t(
            lang, "loan_item",
            icon=icon, name=loan["creditor_name"], amount=loan["amount"],
            currency=loan["currency"], remaining=loan["remaining"],
            date=loan["created_at"].strftime("%d.%m.%Y"),
        ))
    text = t(lang, "loans_list") + "\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=kb.back_kb(lang, "loans"))
    await call.answer()


# ---------- Return loan ----------

@router.callback_query(F.data == "loan:return")
async def loan_return_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    creditors = await db.list_creditors()
    if not creditors:
        await call.answer(t(lang, "no_creditors"), show_alert=True)
        return

    names = sorted(set(c["_id"]["name"] for c in creditors))
    await state.set_state(LoanStates.choosing_creditor_for_return)
    await call.message.edit_text(
        t(lang, "select_creditor"),
        reply_markup=kb.creditors_kb(lang, names, "selectcreditor"),
    )
    await call.answer()


@router.callback_query(LoanStates.choosing_creditor_for_return, F.data.startswith("selectcreditor:"))
async def loan_creditor_selected(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    name = call.data.split(":", 1)[1]
    loans = await db.list_active_loans_by_creditor(name)
    if not loans:
        await call.answer(t(lang, "loan_no_active"), show_alert=True)
        return

    await state.update_data(creditor_name=name)
    await state.set_state(LoanStates.choosing_loan_for_return)
    await call.message.edit_text(
        t(lang, "select_active_loan"),
        reply_markup=kb.loans_select_kb(lang, loans),
    )
    await call.answer()


@router.callback_query(LoanStates.choosing_loan_for_return, F.data.startswith("selectloan:"))
async def loan_selected_for_return(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    loan_id = call.data.split(":")[1]

    from bson import ObjectId
    loan = await db.loans_col.find_one({"_id": ObjectId(loan_id)})

    await state.update_data(loan_id=loan_id, currency=loan["currency"])
    await state.set_state(LoanStates.entering_return_amount)
    await call.message.edit_text(
        t(lang, "enter_return_amount", remaining=loan["remaining"], currency=loan["currency"]),
        reply_markup=kb.cancel_kb(lang),
    )
    await call.answer()


@router.message(LoanStates.entering_return_amount)
async def loan_return_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return

    data = await state.get_data()
    loan_id = data["loan_id"]
    currency = data["currency"]

    result = await db.return_loan_amount(loan_id, amount)
    if result is None:
        await message.answer(t(lang, "invalid_number"))
        return

    remaining, status = result
    name = data["creditor_name"]

    text = t(lang, "loan_returned", amount=amount, currency=currency, name=name, remaining=remaining)
    if status == "done":
        text += "\n\n" + t(lang, "loan_fully_returned", name=name)

    await state.clear()
    await message.answer(text, reply_markup=kb.back_kb(lang, "loans"))