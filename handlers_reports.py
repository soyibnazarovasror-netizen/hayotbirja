"""
Локализация интерфейса: русский и узбекский.
Использование: t(lang, "key") -> строка
Плейсхолдеры форматируются через .format(**kwargs)
"""

TEXTS = {
    "ru": {
        "welcome": "👋 Добро пожаловать в учёт биржи взаимозачёта!\n\nВыберите раздел:",
        "menu_cash": "💰 Касса",
        "menu_loans": "🤝 Займы",
        "menu_lots": "📦 Лоты",
        "menu_reports": "📊 Отчёты",
        "menu_history": "📜 История",
        "menu_lang": "🌐 Тил / Язык",
        "back": "⬅️ Назад",
        "cancel": "❌ Отмена",
        "main_menu": "🏠 Главное меню",

        # Касса
        "cash_title": "💰 Касса\n\nUSD: {usd:.2f} $\nUZS: {uzs:,.0f} сум",
        "cash_add": "➕ Пополнить",
        "cash_withdraw": "➖ Списать",
        "cash_exchange": "🔄 Обмен валюты",
        "choose_currency": "Выберите валюту:",
        "enter_amount": "Введите сумму:",
        "enter_comment": "Комментарий (или отправьте «-» чтобы пропустить):",
        "cash_added": "✅ Касса пополнена: {amount} {currency}",
        "cash_withdrawn": "✅ Списано с кассы: {amount} {currency}",
        "cash_add_reason": "Выберите источник пополнения:",
        "cash_reason_manual": "Прочее пополнение",
        "cash_reason_lot_sale": "Приход от продажи лота",
        "select_lot_for_income": "Выберите лот, от которого получен приход:",

        # Обмен валют
        "exchange_from": "Из какой валюты меняем?",
        "exchange_rate": "Введите курс обмена (сколько UZS за 1 USD):",
        "exchange_done": "✅ Обмен выполнен: {from_amt} {from_cur} → {to_amt:.2f} {to_cur} (курс {rate})",

        # Займы
        "loans_title": "🤝 Займы (инвесторы)\n\nОбщий долг:\nUSD: {usd:.2f} $\nUZS: {uzs:,.0f} сум",
        "loans_list": "📋 Список займов",
        "loan_add": "➕ Новый займ",
        "loan_return": "💵 Вернуть долг",
        "enter_creditor_name": "Введите имя кредитора:",
        "loan_added": "✅ Займ записан: {name} дал {amount} {currency}",
        "select_creditor": "Выберите кредитора:",
        "select_active_loan": "Выберите займ для возврата:",
        "loan_no_active": "Нет активных займов у этого кредитора.",
        "enter_return_amount": "Введите сумму возврата (осталось: {remaining} {currency}):",
        "loan_returned": "✅ Возвращено {amount} {currency} для {name}\nОстаток долга: {remaining} {currency}",
        "loan_fully_returned": "✅ Долг перед {name} полностью погашен! 🎉",
        "no_creditors": "Пока нет ни одного кредитора.",
        "loan_item": "{icon} {name}: {amount} {currency} (осталось {remaining} {currency}) — {date}",
        "loan_status_active": "🔴",
        "loan_status_done": "✅",

        # Лоты
        "lots_title": "📦 Лоты",
        "lot_add": "➕ Новый лот",
        "lot_list_open": "🟡 Открытые лоты",
        "lot_list_closed": "✅ Закрытые лоты",
        "enter_lot_name": "Введите название/номер лота (тендера):",
        "enter_lot_purchase_price": "Введите согласованную сумму по тендеру (за сколько выиграли лот):",
        "lot_created": "✅ Лот «{name}» создан!\nСогласованная сумма по тендеру: {amount} {currency}\nСтатус: 🟡 Открыт\n\nТеперь добавляйте расходы (закупка товара, налог, такси, доставка и т.д.) через кнопку «➕ Добавить расход».",
        "no_lots": "Пока нет лотов.",
        "select_lot": "Выберите лот:",
        "lot_detail": (
            "📦 Лот: {name}\n"
            "Статус: {status}\n"
            "Дата создания: {date}\n\n"
            "📄 Согласовано по тендеру: {purchase:.2f} {currency}\n"
            "📉 Потрачено (расходы): {expenses:.2f} {currency}\n"
        ),
        "lot_detail_closed_extra": (
            "━━━━━━━━━━━━\n"
            "💰 Получено от организации: {sale:.2f} {currency}\n"
            "📈 Прибыль: {profit:.2f} {currency}\n"
        ),
        "lot_add_expense": "➕ Добавить расход",
        "lot_view_expenses": "📋 Список расходов",
        "lot_change_status": "🔁 Изменить статус",
        "lot_close": "🔒 Закрыть лот (продать)",
        "lot_no_expenses": "Расходов пока нет.",
        "expense_item": "• {category}: {amount:.2f} {currency} — {comment} ({date})",
        "choose_expense_category": "Выберите категорию расхода:",
        "cat_purchase": "🛒 Доп. закупка",
        "cat_tax": "🧾 Налог",
        "cat_taxi": "🚕 Такси",
        "cat_delivery": "📦 Доставка",
        "cat_other": "🔹 Прочее",
        "enter_expense_amount": "Введите сумму расхода:",
        "expense_added": "✅ Расход добавлен: {category} — {amount} {currency}",
        "choose_new_status": "Выберите новый статус лота:",
        "status_open": "🟡 Открыт",
        "status_in_progress": "🔵 В работе",
        "status_closed": "✅ Закрыт",
        "status_updated": "✅ Статус обновлён: {status}",
        "enter_sale_price": "Введите сумму, фактически полученную от организации:",
        "lot_closed_result": (
            "🎉 Лот «{name}» закрыт!\n\n"
            "Все расходы: {cost:.2f} {currency}\n"
            "Получено от организации: {sale:.2f} {currency}\n"
            "━━━━━━━━━━━━\n"
            "📈 Прибыль: {profit:.2f} {currency}\n\n"
            "Не забудь занести приход в Кассу через раздел 💰 Касса → Пополнить."
        ),
        "lot_already_closed": "Этот лот уже закрыт.",

        # Отчёты
        "reports_title": "📊 Отчёты",
        "report_summary": "📈 Общая сводка",
        "report_lots_profit": "📦 Прибыль по лотам",
        "report_summary_text": (
            "📊 Общая сводка\n\n"
            "💰 Касса:\nUSD: {cash_usd:.2f} $\nUZS: {cash_uzs:,.0f} сум\n\n"
            "🤝 Долг инвесторам:\nUSD: {debt_usd:.2f} $\nUZS: {debt_uzs:,.0f} сум\n\n"
            "📦 Лотов открыто: {open_lots}\n"
            "✅ Лотов закрыто: {closed_lots}\n\n"
            "📈 Общая прибыль (закрытые лоты):\nUSD: {profit_usd:.2f} $\nUZS: {profit_uzs:,.0f} сум"
        ),
        "no_closed_lots": "Пока нет закрытых лотов.",

        # История
        "history_title": "📜 Последние операции",
        "no_history": "操作пока нет.",
        "history_item": "{icon} {date} — {text}",

        # Общее
        "currency_usd": "USD $",
        "currency_uzs": "UZS сум",
        "invalid_number": "⚠️ Введите корректное число.",
        "operation_cancelled": "Отменено.",
        "skip": "Пропустить",
        "lang_changed": "✅ Язык изменён на русский.",
    },
    "uz": {
        "welcome": "👋 O'zaro hisob-kitob birjasi hisobiga xush kelibsiz!\n\nBo'limni tanlang:",
        "menu_cash": "💰 Kassa",
        "menu_loans": "🤝 Qarzlar",
        "menu_lots": "📦 Lotlar",
        "menu_reports": "📊 Hisobotlar",
        "menu_history": "📜 Tarix",
        "menu_lang": "🌐 Тил / Язык",
        "back": "⬅️ Orqaga",
        "cancel": "❌ Bekor qilish",
        "main_menu": "🏠 Bosh menyu",

        "cash_title": "💰 Kassa\n\nUSD: {usd:.2f} $\nUZS: {uzs:,.0f} so'm",
        "cash_add": "➕ To'ldirish",
        "cash_withdraw": "➖ Yechish",
        "cash_exchange": "🔄 Valyuta almashish",
        "choose_currency": "Valyutani tanlang:",
        "enter_amount": "Summani kiriting:",
        "enter_comment": "Izoh (yoki «-» yuboring, o'tkazib yuborish uchun):",
        "cash_added": "✅ Kassaga qo'shildi: {amount} {currency}",
        "cash_withdrawn": "✅ Kassadan yechildi: {amount} {currency}",
        "cash_add_reason": "To'ldirish manbasini tanlang:",
        "cash_reason_manual": "Boshqa tushum",
        "cash_reason_lot_sale": "Lot sotuvidan tushum",
        "select_lot_for_income": "Qaysi lotdan tushum olindi?",

        "exchange_from": "Qaysi valyutadan almashtiramiz?",
        "exchange_rate": "Kursni kiriting (1 USD nechchi UZS):",
        "exchange_done": "✅ Almashtirildi: {from_amt} {from_cur} → {to_amt:.2f} {to_cur} (kurs {rate})",

        "loans_title": "🤝 Qarzlar (investorlar)\n\nUmumiy qarz:\nUSD: {usd:.2f} $\nUZS: {uzs:,.0f} so'm",
        "loans_list": "📋 Qarzlar ro'yxati",
        "loan_add": "➕ Yangi qarz",
        "loan_return": "💵 Qarzni qaytarish",
        "enter_creditor_name": "Kreditor ismini kiriting:",
        "loan_added": "✅ Qarz yozildi: {name} {amount} {currency} berdi",
        "select_creditor": "Kreditorni tanlang:",
        "select_active_loan": "Qaytarish uchun qarzni tanlang:",
        "loan_no_active": "Bu kreditorning faol qarzi yo'q.",
        "enter_return_amount": "Qaytarish summasini kiriting (qoldiq: {remaining} {currency}):",
        "loan_returned": "✅ {name} uchun {amount} {currency} qaytarildi\nQarz qoldig'i: {remaining} {currency}",
        "loan_fully_returned": "✅ {name} oldidagi qarz to'liq yopildi! 🎉",
        "no_creditors": "Hozircha kreditorlar yo'q.",
        "loan_item": "{icon} {name}: {amount} {currency} (qoldi {remaining} {currency}) — {date}",
        "loan_status_active": "🔴",
        "loan_status_done": "✅",

        "lots_title": "📦 Lotlar",
        "lot_add": "➕ Yangi lot",
        "lot_list_open": "🟡 Ochiq lotlar",
        "lot_list_closed": "✅ Yopilgan lotlar",
        "enter_lot_name": "Lot (tender) nomi/raqamini kiriting:",
        "enter_lot_purchase_price": "Tenderda kelishilgan summani kiriting (qancha summaga lotni yutib oldingiz):",
        "lot_created": "✅ «{name}» loti yaratildi!\nTenderda kelishilgan summa: {amount} {currency}\nHolat: 🟡 Ochiq\n\nEndi xarajatlarni qo'shib boring (tovar xaridi, soliq, taksi, yetkazib berish va h.k.) «➕ Xarajat qo'shish» tugmasi orqali.",
        "no_lots": "Hozircha lotlar yo'q.",
        "select_lot": "Lotni tanlang:",
        "lot_detail": (
            "📦 Lot: {name}\n"
            "Holat: {status}\n"
            "Yaratilgan sana: {date}\n\n"
            "📄 Tenderda kelishilgan: {purchase:.2f} {currency}\n"
            "📉 Sarflangan (xarajatlar): {expenses:.2f} {currency}\n"
        ),
        "lot_detail_closed_extra": (
            "━━━━━━━━━━━━\n"
            "💰 Tashkilotdan olingan: {sale:.2f} {currency}\n"
            "📈 Foyda: {profit:.2f} {currency}\n"
        ),
        "lot_add_expense": "➕ Xarajat qo'shish",
        "lot_view_expenses": "📋 Xarajatlar ro'yxati",
        "lot_change_status": "🔁 Holatni o'zgartirish",
        "lot_close": "🔒 Lotni yopish (sotish)",
        "lot_no_expenses": "Hozircha xarajat yo'q.",
        "expense_item": "• {category}: {amount:.2f} {currency} — {comment} ({date})",
        "choose_expense_category": "Xarajat turini tanlang:",
        "cat_purchase": "🛒 Qo'shimcha xarid",
        "cat_tax": "🧾 Soliq",
        "cat_taxi": "🚕 Taksi",
        "cat_delivery": "📦 Yetkazib berish",
        "cat_other": "🔹 Boshqa",
        "enter_expense_amount": "Xarajat summasini kiriting:",
        "expense_added": "✅ Xarajat qo'shildi: {category} — {amount} {currency}",
        "choose_new_status": "Lotning yangi holatini tanlang:",
        "status_open": "🟡 Ochiq",
        "status_in_progress": "🔵 Jarayonda",
        "status_closed": "✅ Yopilgan",
        "status_updated": "✅ Holat yangilandi: {status}",
        "enter_sale_price": "Tashkilotdan haqiqatda olingan summani kiriting:",
        "lot_closed_result": (
            "🎉 «{name}» loti yopildi!\n\n"
            "Barcha xarajatlar: {cost:.2f} {currency}\n"
            "Tashkilotdan olingan: {sale:.2f} {currency}\n"
            "━━━━━━━━━━━━\n"
            "📈 Foyda: {profit:.2f} {currency}\n\n"
            "Tushumni Kassaga qo'shishni unutmang: 💰 Kassa → To'ldirish."
        ),
        "lot_already_closed": "Bu lot allaqachon yopilgan.",

        "reports_title": "📊 Hisobotlar",
        "report_summary": "📈 Umumiy hisobot",
        "report_lots_profit": "📦 Lotlar bo'yicha foyda",
        "report_summary_text": (
            "📊 Umumiy hisobot\n\n"
            "💰 Kassa:\nUSD: {cash_usd:.2f} $\nUZS: {cash_uzs:,.0f} so'm\n\n"
            "🤝 Investorlar oldidagi qarz:\nUSD: {debt_usd:.2f} $\nUZS: {debt_uzs:,.0f} so'm\n\n"
            "📦 Ochiq lotlar: {open_lots}\n"
            "✅ Yopilgan lotlar: {closed_lots}\n\n"
            "📈 Umumiy foyda (yopilgan lotlar):\nUSD: {profit_usd:.2f} $\nUZS: {profit_uzs:,.0f} so'm"
        ),
        "no_closed_lots": "Hozircha yopilgan lot yo'q.",

        "history_title": "📜 So'nggi operatsiyalar",
        "no_history": "Hozircha operatsiya yo'q.",
        "history_item": "{icon} {date} — {text}",

        "currency_usd": "USD $",
        "currency_uzs": "UZS so'm",
        "invalid_number": "⚠️ To'g'ri son kiriting.",
        "operation_cancelled": "Bekor qilindi.",
        "skip": "O'tkazib yuborish",
        "lang_changed": "✅ Til o'zbekchaga o'zgartirildi.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TEXTS else "ru"
    template = TEXTS[lang].get(key, TEXTS["ru"].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template
