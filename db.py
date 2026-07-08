"""
Слой работы с MongoDB Atlas.
Коллекции:
  - users        {user_id, lang, created_at}
  - cash         {_id: "balance", USD: float, UZS: float}
  - loans        {_id, creditor_name, amount, currency, remaining, status, created_at, returns: [...]}
  - lots         {_id, name, purchase_amount, purchase_currency, status, created_at,
                   expenses: [{category, amount, currency, comment, date}],
                   sale_amount, sale_currency, closed_at, profit}
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


# ---------- Lots ----------

async def create_lot(name: str, purchase_amount: float, currency: str) -> str:
    doc = {
        "name": name,
        "purchase_amount": purchase_amount,
        "purchase_currency": currency,
        "status": "open",
        "created_at": now(),
        "expenses": [],
        "sale_amount": None,
        "sale_currency": None,
        "closed_at": None,
        "profit": None,
    }
    result = await lots_col.insert_one(doc)
    await adjust_cash(currency, -purchase_amount)
    await add_history("lot_create", f"Лот «{name}»: покупка {purchase_amount} {currency}")
    return str(result.inserted_id)


async def list_lots(status: str = None) -> list:
    query = {"status": status} if status else {}
    cursor = lots_col.find(query).sort("created_at", -1)
    return [doc async for doc in cursor]


async def get_lot(lot_id):
    from bson import ObjectId
    return await lots_col.find_one({"_id": ObjectId(lot_id)})


async def add_lot_expense(lot_id, category: str, amount: float, currency: str, comment: str):
    from bson import ObjectId
    expense = {"category": category, "amount": amount, "currency": currency, "comment": comment, "date": now()}
    await lots_col.update_one({"_id": ObjectId(lot_id)}, {"$push": {"expenses": expense}})
    await adjust_cash(currency, -amount)
    lot = await get_lot(lot_id)
    await add_history("lot_expense", f"Лот «{lot['name']}»: расход {category} {amount} {currency}")


async def set_lot_status(lot_id, status: str):
    from bson import ObjectId
    await lots_col.update_one({"_id": ObjectId(lot_id)}, {"$set": {"status": status}})


async def close_lot(lot_id, sale_amount: float, sale_currency: str):
    from bson import ObjectId
    lot = await get_lot(lot_id)
    if not lot:
        return None
    total_expenses = sum(e["amount"] for e in lot["expenses"] if e["currency"] == sale_currency)
    purchase = lot["purchase_amount"] if lot["purchase_currency"] == sale_currency else 0
    cost = purchase + total_expenses
    profit = round(sale_amount - cost, 2)
    await lots_col.update_one(
        {"_id": ObjectId(lot_id)},
        {"$set": {
            "status": "closed",
            "sale_amount": sale_amount,
            "sale_currency": sale_currency,
            "closed_at": now(),
            "profit": profit,
        }},
    )
    await add_history("lot_close", f"Лот «{lot['name']}» закрыт: прибыль {profit} {sale_currency}")
    return cost, profit


def lot_total_cost(lot: dict, currency: str) -> float:
    purchase = lot["purchase_amount"] if lot["purchase_currency"] == currency else 0
    expenses = sum(e["amount"] for e in lot["expenses"] if e["currency"] == currency)
    return purchase + expenses


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
        {"$group": {"_id": "$sale_currency", "total_profit": {"$sum": "$profit"}}}
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
