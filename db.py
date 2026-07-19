"""
Слой работы с MongoDB Atlas.
Коллекции:
  - users        {user_id, lang, created_at}
  - cash         {_id: "balance", USD: float, UZS: float}
  - loans        {_id, creditor_name, amount, currency, remaining, status, created_at, returns: [...]}
  - lots         {_id, name, agreed_amount, currency, status, created_at,
                   expenses: [{category, amount, currency, comment, date}],
                   received_amount, received_currency, closed_at, profit}
  - history      {_id, type, text, date}
"""

import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "loanbot")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
cash_col = db["cash"]
loans_col = db["loans"]
lots_col = db["lots"]
history_col = db["history"]


def now():
    return datetime.now(timezone.utc)


# ---------- Users / language ----------

async def get_user_lang(user_id: int) -> str:
    user = await users_col.find_one({"user_id": user_id})
    if user:
        return user.get("lang", "ru")
    await users_col.insert_one({"user_id": user_id, "lang": "ru", "created_at": now()})
    return "ru"


async def set_user_lang(user_id: int, lang: str):
    await users_col.update_one(
        {"user_id": user_id}, {"$set": {"lang": lang}}, upsert=True
    )


# ---------- Cash ----------

async def get_cash() -> dict:
    doc = await cash_col.find_one({"_id": "balance"})
    if not doc:
        doc = {"_id": "balance", "USD": 0.0, "UZS": 0.0}
        await cash_col.insert_one(doc)
        return doc
    # На случай если документ уже существует, но без одного из полей
    # (например, если баланс создался через $inc только по одной валюте)
    if "USD" not in doc or "UZS" not in doc:
        doc.setdefault("USD", 0.0)
        doc.setdefault("UZS", 0.0)
        await cash_col.update_one(
            {"_id": "balance"},
            {"$set": {"USD": doc["USD"], "UZS": doc["UZS"]}},
            upsert=True,
        )
    return doc


async def adjust_cash(currency: str, delta: float):
    await cash_col.update_one(
        {"_id": "balance"}, {"$inc": {currency: delta}}, upsert=True
    )


# ---------- Loans ----------

async def create_loan(creditor_name: str, amount: float, currency: str) -> str:
    doc = {
        "creditor_name": creditor_name,
        "amount": amount,
        "currency": currency,
        "remaining": amount,
        "status": "active",
        "created_at": now(),
        "returns": [],
    }
    result = await loans_col.insert_one(doc)
    await adjust_cash(currency, amount)
    await add_history("loan_in", f"{creditor_name}: +{amount} {currency}")
    return str(result.inserted_id)


async def list_creditors() -> list:
    """Уникальные имена кредиторов с суммой активного долга"""
    cursor = loans_col.aggregate([
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": {"name": "$creditor_name", "currency": "$currency"},
            "total_remaining": {"$sum": "$remaining"}
        }}
    ])
    return [doc async for doc in cursor]


async def list_all_loans() -> list:
    cursor = loans_col.find().sort("created_at", -1)
    return [doc async for doc in cursor]


async def list_active_loans_by_creditor(creditor_name: str) -> list:
    cursor = loans_col.find({"creditor_name": creditor_name, "status": "active"}).sort("created_at", 1)
    return [doc async for doc in cursor]


async def get_total_debt() -> dict:
    cursor = loans_col.aggregate([
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$currency", "total": {"$sum": "$remaining"}}}
    ])
    result = {"USD": 0.0, "UZS": 0.0}
    async for doc in cursor:
        result[doc["_id"]] = doc["total"]
    return result


async def return_loan_amount(loan_id, amount: float):
    from bson import ObjectId
    loan = await loans_col.find_one({"_id": ObjectId(loan_id)})
    if not loan:
        return None
    new_remaining = round(loan["remaining"] - amount, 2)
    new_status = "done" if new_remaining <= 0.009 else "active"
    await loans_col.update_one(
        {"_id": ObjectId(loan_id)},
        {
            "$set": {"remaining": max(new_remaining, 0), "status": new_status},
            "$push": {"returns": {"amount": amount, "date": now()}},
        },
    )
    await adjust_cash(loan["currency"], -amount)
    await add_history("loan_return", f"{loan['creditor_name']}: -{amount} {loan['currency']}")
    return new_remaining, new_status


async def update_loan_amount(loan_id, new_amount: float):
    """Меняем изначальную сумму займа (например, если ввели неверно).
    Остаток долга пересчитывается с учётом уже сделанных возвратов,
    а касса корректируется на разницу."""
    from bson import ObjectId
    loan = await loans_col.find_one({"_id": ObjectId(loan_id)})
    if not loan:
        return None
    already_returned = loan["amount"] - loan["remaining"]
    new_remaining = round(new_amount - already_returned, 2)
    new_status = "done" if new_remaining <= 0.009 else "active"
    delta = new_amount - loan["amount"]  # разница уходит в кассу
    await loans_col.update_one(
        {"_id": ObjectId(loan_id)},
        {"$set": {"amount": new_amount, "remaining": max(new_remaining, 0), "status": new_status}},
    )
    await adjust_cash(loan["currency"], delta)
    await add_history(
        "loan_edit",
        f"{loan['creditor_name']}: сумма займа изменена {loan['amount']} → {new_amount} {loan['currency']}",
    )
    return new_remaining, new_status


async def delete_loan(loan_id):
    """Полностью удаляем займ. Из кассы вычитается его текущий непогашенный остаток
    (эффект от суммы займа и уже сделанных возвратов взаимно гасится)."""
    from bson import ObjectId
    loan = await loans_col.find_one({"_id": ObjectId(loan_id)})
    if not loan:
        return None
    await adjust_cash(loan["currency"], -loan["remaining"])
    await loans_col.delete_one({"_id": ObjectId(loan_id)})
    await add_history("loan_delete", f"Займ {loan['creditor_name']} ({loan['amount']} {loan['currency']}) удалён")
    return loan


# ---------- Lots ----------
# Механика тендера: при создании лота деньги НЕ списываются с кассы —
# agreed_amount это лишь справочная сумма, за которую выигран тендер.
# Реальные траты идут через expenses (закупка товара, налог, такси, доставка и т.д.).
# При закрытии лота вводится фактически полученная от организации сумма,
# и прибыль = полученная сумма - сумма всех расходов.

async def create_lot(name: str, agreed_amount: float, currency: str) -> str:
    doc = {
        "name": name,
        "agreed_amount": agreed_amount,
        "currency": currency,
        "status": "open",
        "created_at": now(),
        "expenses": [],
        "received_amount": None,
        "received_currency": None,
        "closed_at": None,
        "profit": None,
    }
    result = await lots_col.insert_one(doc)
    await add_history("lot_create", f"Лот «{name}»: согласованная сумма {agreed_amount} {currency}")
    return str(result.inserted_id)


async def list_lots(status: str = None) -> list:
    query = {"status": status} if status else {}
    cursor = lots_col.find(query).sort("created_at", -1)
    return [doc async for doc in cursor]


async def get_lot(lot_id):
    from bson import ObjectId
    lot = await lots_col.find_one({"_id": ObjectId(lot_id)})
    if not lot:
        return None
    # Миграция: у расходов, добавленных до введения id, проставляем его на лету
    needs_fix = False
    for e in lot["expenses"]:
        if "id" not in e:
            e["id"] = str(ObjectId())
            needs_fix = True
    if needs_fix:
        await lots_col.update_one({"_id": ObjectId(lot_id)}, {"$set": {"expenses": lot["expenses"]}})
    return lot


async def add_lot_expense(lot_id, category: str, amount: float, currency: str, comment: str):
    from bson import ObjectId
    expense = {
        "id": str(ObjectId()),
        "category": category, "amount": amount, "currency": currency,
        "comment": comment, "date": now(),
    }
    await lots_col.update_one({"_id": ObjectId(lot_id)}, {"$push": {"expenses": expense}})
    await adjust_cash(currency, -amount)
    lot = await get_lot(lot_id)
    await add_history("lot_expense", f"Лот «{lot['name']}»: расход {category} {amount} {currency}")


async def update_lot_expense(lot_id, expense_id: str, new_amount: float):
    """Меняем сумму расхода и корректируем кассу на разницу."""
    from bson import ObjectId
    lot = await get_lot(lot_id)
    if not lot:
        return None
    expense = next((e for e in lot["expenses"] if e.get("id") == expense_id), None)
    if not expense:
        return None
    old_amount = expense["amount"]
    delta = old_amount - new_amount  # если новая сумма больше — с кассы спишется ещё
    await lots_col.update_one(
        {"_id": ObjectId(lot_id), "expenses.id": expense_id},
        {"$set": {"expenses.$.amount": new_amount}},
    )
    await adjust_cash(expense["currency"], delta)
    await add_history(
        "lot_expense_edit",
        f"Лот «{lot['name']}»: расход изменён {old_amount} → {new_amount} {expense['currency']}",
    )
    return expense


async def delete_lot_expense(lot_id, expense_id: str):
    """Удаляем расход и возвращаем сумму в кассу."""
    from bson import ObjectId
    lot = await get_lot(lot_id)
    if not lot:
        return None
    expense = next((e for e in lot["expenses"] if e.get("id") == expense_id), None)
    if not expense:
        return None
    await lots_col.update_one(
        {"_id": ObjectId(lot_id)},
        {"$pull": {"expenses": {"id": expense_id}}},
    )
    await adjust_cash(expense["currency"], expense["amount"])
    await add_history(
        "lot_expense_delete",
        f"Лот «{lot['name']}»: удалён расход {expense['amount']} {expense['currency']}",
    )
    return expense


async def set_lot_status(lot_id, status: str):
    from bson import ObjectId
    await lots_col.update_one({"_id": ObjectId(lot_id)}, {"$set": {"status": status}})


async def close_lot(lot_id, received_amount: float, received_currency: str):
    """Закрытие лота: сумма от организации сразу зачисляется в кассу."""
    from bson import ObjectId
    lot = await get_lot(lot_id)
    if not lot:
        return None
    total_expenses = sum(e["amount"] for e in lot["expenses"] if e["currency"] == received_currency)
    profit = round(received_amount - total_expenses, 2)
    await lots_col.update_one(
        {"_id": ObjectId(lot_id)},
        {"$set": {
            "status": "closed",
            "received_amount": received_amount,
            "received_currency": received_currency,
            "closed_at": now(),
            "profit": profit,
        }},
    )
    await adjust_cash(received_currency, received_amount)
    await add_history("lot_close", f"Лот «{lot['name']}» закрыт: получено {received_amount} {received_currency}, прибыль {profit}")
    return total_expenses, profit


def lot_total_cost(lot: dict, currency: str) -> float:
    """Сумма всех расходов лота в заданной валюте (закупка товара тоже проходит как расход)."""
    return sum(e["amount"] for e in lot["expenses"] if e["currency"] == currency)


async def update_lot_agreed_amount(lot_id, new_amount: float):
    """Меняем справочную согласованную сумму по тендеру (на кассу не влияет)."""
    from bson import ObjectId
    await lots_col.update_one({"_id": ObjectId(lot_id)}, {"$set": {"agreed_amount": new_amount}})
    lot = await get_lot(lot_id)
    await add_history("lot_edit", f"Лот «{lot['name']}»: согласованная сумма изменена на {new_amount} {lot['currency']}")


async def update_lot_received(lot_id, new_received_amount: float):
    """Меняем сумму, полученную от организации: пересчитываем прибыль и корректируем кассу на разницу."""
    from bson import ObjectId
    lot = await get_lot(lot_id)
    if not lot or lot["status"] != "closed":
        return None
    total_expenses = sum(e["amount"] for e in lot["expenses"] if e["currency"] == lot["received_currency"])
    new_profit = round(new_received_amount - total_expenses, 2)
    delta = new_received_amount - lot["received_amount"]
    await lots_col.update_one(
        {"_id": ObjectId(lot_id)},
        {"$set": {"received_amount": new_received_amount, "profit": new_profit}},
    )
    await adjust_cash(lot["received_currency"], delta)
    await add_history(
        "lot_edit",
        f"Лот «{lot['name']}»: сумма от организации изменена на {new_received_amount} {lot['received_currency']}",
    )
    return new_profit


async def delete_lot(lot_id):
    """Полностью удаляем лот. Возвращаем в кассу все его расходы,
    и если лот был закрыт — списываем ранее зачисленную сумму от организации."""
    from bson import ObjectId
    lot = await get_lot(lot_id)
    if not lot:
        return None
    for e in lot["expenses"]:
        await adjust_cash(e["currency"], e["amount"])
    if lot["status"] == "closed" and lot.get("received_amount"):
        await adjust_cash(lot["received_currency"], -lot["received_amount"])
    await lots_col.delete_one({"_id": ObjectId(lot_id)})
    await add_history("lot_delete", f"Лот «{lot['name']}» удалён")
    return lot


# ---------- History ----------

async def add_history(type_: str, text: str):
    await history_col.insert_one({"type": type_, "text": text, "date": now()})


async def get_recent_history(limit: int = 15) -> list:
    cursor = history_col.find().sort("date", -1).limit(limit)
    return [doc async for doc in cursor]


# ---------- Reports ----------

async def get_lots_profit_summary() -> dict:
    cursor = lots_col.aggregate([
        {"$match": {"status": "closed"}},
        {"$group": {"_id": "$received_currency", "total_profit": {"$sum": "$profit"}}}
    ])
    result = {"USD": 0.0, "UZS": 0.0}
    async for doc in cursor:
        if doc["_id"] in result:
            result[doc["_id"]] = doc["total_profit"]
    return result


async def count_lots_by_status() -> dict:
    open_count = await lots_col.count_documents({"status": {"$in": ["open", "in_progress"]}})
    closed_count = await lots_col.count_documents({"status": "closed"})
    return {"open": open_count, "closed": closed_count}


async def get_lots_cash_movements() -> list:
    """Для раздела Касса: по каждому лоту — сумма расходов и (если закрыт) приход от организации."""
    cursor = lots_col.find().sort("created_at", -1)
    result = []
    async for lot in cursor:
        expenses_by_cur = {}
        for e in lot["expenses"]:
            expenses_by_cur[e["currency"]] = expenses_by_cur.get(e["currency"], 0) + e["amount"]
        result.append({
            "name": lot["name"],
            "status": lot["status"],
            "expenses": expenses_by_cur,
            "received_amount": lot.get("received_amount"),
            "received_currency": lot.get("received_currency"),
        })
    return result
