import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import db
import keyboards as kb
from i18n import t

import handlers_cash
import handlers_loans
import handlers_lots
import handlers_reports

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    lang = await db.get_user_lang(message.from_user.id)
    await message.answer(t(lang, "welcome"), reply_markup=kb.main_menu_kb(lang))


@router.callback_query(F.data == "back:main")
async def back_to_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await db.get_user_lang(call.from_user.id)
    await call.message.edit_text(t(lang, "welcome"), reply_markup=kb.main_menu_kb(lang))
    await call.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(call: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await db.get_user_lang(call.from_user.id)
    await call.message.edit_text(t(lang, "welcome"), reply_markup=kb.main_menu_kb(lang))
    await call.answer(t(lang, "operation_cancelled"))


@router.callback_query(F.data == "menu:lang")
async def open_lang_menu(call: CallbackQuery):
    await call.message.edit_text("🌐 Til / Язык:", reply_markup=kb.lang_kb())
    await call.answer()


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    await db.set_user_lang(call.from_user.id, lang)
    await state.clear()
    await call.message.edit_text(t(lang, "lang_changed"), reply_markup=kb.back_kb(lang, "main"))
    await call.answer()


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)
    dp.include_router(handlers_cash.router)
    dp.include_router(handlers_loans.router)
    dp.include_router(handlers_lots.router)
    dp.include_router(handlers_reports.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())