from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
from i18n import t
from states import LotStates

router = Router()

STATUS_KEY = {"open": "status_open", "in_progress": "status_in_progress", "closed": "status_closed"}
CAT_KEY = {
    "purchase": "cat_purchase", "tax": "cat_tax", "taxi": "cat_taxi",
    "delivery": "cat_delivery", "other": "cat_other",
}


async def show_lots_menu(target, lang: str, edit: bool = True):
    text = t(lang, "lots_title")
    markup = kb.lots_menu_kb(lang)
    if edit:
        await target.message.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.callback_query(F.data == "menu:lots")
async def open_lots_menu(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.clear()
    await show_lots_menu(call, lang)
    await call.answer()


@router.callback_query(F.data == "back:lots")
async def back_to_lots(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.clear()
    await show_lots_menu(call, lang)
    await call.answer()


# ---------- Create lot ----------

@router.callback_query(F.data == "lot:add")
async def lot_add_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    await state.set_state(LotStates.entering_name)
    await call.message.edit_text(t(lang, "enter_lot_name"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(LotStates.entering_name)
async def lot_name_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(LotStates.choosing_currency)
    await message.answer(t(lang, "choose_currency"), reply_markup=kb.currency_kb(lang, "lotcurrency"))


@router.callback_query(LotStates.choosing_currency, F.data.startswith("lotcurrency:"))
async def lot_currency_chosen(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    currency = call.data.split(":")[1]
    await state.update_data(currency=currency)
    await state.set_state(LotStates.entering_purchase_amount)
    await call.message.edit_text(t(lang, "enter_lot_purchase_price"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(LotStates.entering_purchase_amount)
async def lot_purchase_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return

    data = await state.get_data()
    name = data["name"]
    currency = data["currency"]

    await db.create_lot(name, amount, currency)
    text = t(lang, "lot_created", name=name, amount=amount, currency=currency)
    await state.clear()
    await message.answer(text, reply_markup=kb.back_kb(lang, "lots"))


# ---------- List lots ----------

@router.callback_query(F.data == "lot:list_open")
async def lot_list_open(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    lots = await db.list_lots()
    lots = [l for l in lots if l["status"] in ("open", "in_progress")]
    if not lots:
        await call.message.edit_text(t(lang, "no_lots"), reply_markup=kb.back_kb(lang, "lots"))
    else:
        await call.message.edit_text(t(lang, "lot_list_open"), reply_markup=kb.lots_list_kb(lang, lots))
    await call.answer()


@router.callback_query(F.data == "lot:list_closed")
async def lot_list_closed(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    lots = await db.list_lots(status="closed")
    if not lots:
        await call.message.edit_text(t(lang, "no_lots"), reply_markup=kb.back_kb(lang, "lots"))
    else:
        await call.message.edit_text(t(lang, "lot_list_closed"), reply_markup=kb.lots_list_kb(lang, lots))
    await call.answer()


# ---------- View lot detail ----------

async def render_lot_detail(lang: str, lot: dict) -> str:
    currency = lot["purchase_currency"]
    total_expenses = sum(e["amount"] for e in lot["expenses"] if e["currency"] == currency)
    total = lot["purchase_amount"] + total_expenses
    status_text = t(lang, STATUS_KEY.get(lot["status"], "status_open"))

    text = t(
        lang, "lot_detail",
        name=lot["name"], status=status_text,
        date=lot["created_at"].strftime("%d.%m.%Y"),
        purchase=lot["purchase_amount"], expenses=total_expenses,
        currency=currency, total=total,
    )
    if lot["status"] == "closed":
        text += t(
            lang, "lot_detail_closed_extra",
            sale=lot["sale_amount"], currency=lot["sale_currency"], profit=lot["profit"],
        )
    return text


@router.callback_query(F.data.startswith("viewlot:"))
async def view_lot(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    lot_id = call.data.split(":")[1]
    lot = await db.get_lot(lot_id)
    if not lot:
        await call.answer()
        return

    await state.update_data(current_lot_id=lot_id)
    text = await render_lot_detail(lang, lot)
    await call.message.edit_text(text, reply_markup=kb.lot_detail_kb(lang, lot_id, lot["status"]))
    await call.answer()


# ---------- Add expense ----------

@router.callback_query(F.data.startswith("lotaction:expense:"))
async def lot_expense_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    lot_id = call.data.split(":")[2]
    await state.update_data(current_lot_id=lot_id)
    await state.set_state(LotStates.choosing_expense_category)
    await call.message.edit_text(t(lang, "choose_expense_category"), reply_markup=kb.expense_category_kb(lang))
    await call.answer()


@router.callback_query(LotStates.choosing_expense_category, F.data.startswith("expcat:"))
async def lot_expense_category_chosen(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    category = call.data.split(":")[1]
    await state.update_data(category=category)
    await state.set_state(LotStates.entering_expense_currency)
    await call.message.edit_text(t(lang, "choose_currency"), reply_markup=kb.currency_kb(lang, "expcurrency"))
    await call.answer()


@router.callback_query(LotStates.entering_expense_currency, F.data.startswith("expcurrency:"))
async def lot_expense_currency_chosen(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    currency = call.data.split(":")[1]
    await state.update_data(currency=currency)
    await state.set_state(LotStates.entering_expense_amount)
    await call.message.edit_text(t(lang, "enter_expense_amount"), reply_markup=kb.cancel_kb(lang))
    await call.answer()


@router.message(LotStates.entering_expense_amount)
async def lot_expense_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return
    await state.update_data(amount=amount)
    await state.set_state(LotStates.entering_expense_comment)
    await message.answer(t(lang, "enter_comment"), reply_markup=kb.skip_comment_kb(lang))


@router.callback_query(LotStates.entering_expense_comment, F.data == "skip_comment")
async def lot_expense_comment_skipped(call: CallbackQuery, state: FSMContext):
    await finalize_expense(call.message, state, call.from_user.id, comment="-")
    await call.answer()


@router.message(LotStates.entering_expense_comment)
async def lot_expense_comment_entered(message: Message, state: FSMContext):
    comment = message.text.strip()
    await finalize_expense(message, state, message.from_user.id, comment=comment)


async def finalize_expense(message_target, state: FSMContext, user_id: int, comment: str):
    lang = await db.get_user_lang(user_id)
    data = await state.get_data()
    lot_id = data["current_lot_id"]
    category = data["category"]
    amount = data["amount"]
    currency = data["currency"]

    await db.add_lot_expense(lot_id, category, amount, currency, comment)
    category_label = t(lang, CAT_KEY.get(category, "cat_other"))
    text = t(lang, "expense_added", category=category_label, amount=amount, currency=currency)

    await state.set_state(None)
    lot = await db.get_lot(lot_id)
    detail_text = await render_lot_detail(lang, lot)
    full_text = text + "\n\n" + detail_text

    if isinstance(message_target, Message):
        await message_target.answer(full_text, reply_markup=kb.lot_detail_kb(lang, lot_id, lot["status"]))
    else:
        await message_target.edit_text(full_text, reply_markup=kb.lot_detail_kb(lang, lot_id, lot["status"]))


# ---------- View expenses ----------

@router.callback_query(F.data.startswith("lotaction:viewexp:"))
async def lot_view_expenses(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    lot_id = call.data.split(":")[2]
    lot = await db.get_lot(lot_id)

    if not lot["expenses"]:
        text = t(lang, "lot_no_expenses")
    else:
        lines = []
        for e in lot["expenses"]:
            cat_label = t(lang, CAT_KEY.get(e["category"], "cat_other"))
            lines.append(t(
                lang, "expense_item",
                category=cat_label, amount=e["amount"], currency=e["currency"],
                comment=e["comment"], date=e["date"].strftime("%d.%m.%Y"),
            ))
        text = "\n".join(lines)

    await call.message.edit_text(text, reply_markup=kb.lot_detail_kb(lang, lot_id, lot["status"]))
    await call.answer()


# ---------- Change status ----------

@router.callback_query(F.data.startswith("lotaction:status:"))
async def lot_status_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    lot_id = call.data.split(":")[2]
    await call.message.edit_text(t(lang, "choose_new_status"), reply_markup=kb.lot_status_kb(lang, lot_id))
    await call.answer()


@router.callback_query(F.data.startswith("setstatus:"))
async def lot_status_set(call: CallbackQuery):
    lang = await db.get_user_lang(call.from_user.id)
    _, lot_id, status = call.data.split(":")
    await db.set_lot_status(lot_id, status)
    lot = await db.get_lot(lot_id)
    status_text = t(lang, STATUS_KEY.get(status, "status_open"))
    text = t(lang, "status_updated", status=status_text) + "\n\n" + await render_lot_detail(lang, lot)
    await call.message.edit_text(text, reply_markup=kb.lot_detail_kb(lang, lot_id, lot["status"]))
    await call.answer()


# ---------- Close lot ----------

@router.callback_query(F.data.startswith("lotaction:close:"))
async def lot_close_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_user_lang(call.from_user.id)
    lot_id = call.data.split(":")[2]
    lot = await db.get_lot(lot_id)

    if lot["status"] == "closed":
        await call.answer(t(lang, "lot_already_closed"), show_alert=True)
        return

    await state.update_data(current_lot_id=lot_id, sale_currency=lot["purchase_currency"])
    await state.set_state(LotStates.entering_sale_amount)
    await call.message.edit_text(
        t(lang, "enter_sale_price"),
        reply_markup=kb.cancel_kb(lang),
    )
    await call.answer()


@router.message(LotStates.entering_sale_amount)
async def lot_sale_amount_entered(message: Message, state: FSMContext):
    lang = await db.get_user_lang(message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "invalid_number"))
        return

    data = await state.get_data()
    lot_id = data["current_lot_id"]
    currency = data["sale_currency"]

    lot = await db.get_lot(lot_id)
    cost, profit = await db.close_lot(lot_id, amount, currency)

    text = t(
        lang, "lot_closed_result",
        name=lot["name"], cost=cost, sale=amount, profit=profit, currency=currency,
    )
    await state.clear()
    await message.answer(text, reply_markup=kb.back_kb(lang, "lots"))