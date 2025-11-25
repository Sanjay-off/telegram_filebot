from pymongo import MongoClient
from datetime import datetime, timedelta
from .config import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["telegram_filebot"]

users_col = db["users"]
payments_col = db["payments"]
settings_col = db["settings"]

DEFAULT_SETTINGS = {
    "verify_link": "https://t.me/yourchannel/123",   # How to verify video/message
    "delete_time_minutes": 10,                       # Auto delete file after X minutes
    "verification_days": 1,                          # Verification validity (days)
    "free_downloads": 3,                             # Free downloads per verification
    "zip_password": "Legalstuff321",                 # Default ZIP password
    "premium_minutes": 1440,                         # Example: 1-day premium
}

def get_user(user_id: int) -> dict:
    user = users_col.find_one({"_id": user_id})
    if not user:
        user = {
            "_id": user_id,
            "is_premium": False,
            "premium_until": None,
            "is_verified": False,
            "verified_until": None,
            "downloads_left": 0,
            "last_file_code": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        users_col.insert_one(user)
    return user

def update_user(user_id: int, data: dict):
    data["updated_at"] = datetime.utcnow()
    users_col.update_one({"_id": user_id}, {"$set": data}, upsert=True)

def get_settings() -> dict:
    doc = settings_col.find_one({"_id": "global"})
    if not doc:
        doc = {"_id": "global", **DEFAULT_SETTINGS}
        settings_col.insert_one(doc)
    merged = dict(DEFAULT_SETTINGS)
    merged.update({k: v for k, v in doc.items() if k != "_id"})
    return merged

def set_setting(key: str, value):
    settings_col.update_one({"_id": "global"}, {"$set": {key: value}}, upsert=True)

def count_users():
    total = users_col.count_documents({})
    verified = users_col.count_documents({"is_verified": True})
    premium = users_col.count_documents({"is_premium": True})
    return total, verified, premium

def create_payment(user_id: int, plan_name: str, amount: int) -> str:
    """Create payment order (skeleton). Returns order_id."""
    now = datetime.utcnow()
    order_id = f"ORD-{user_id}-{int(now.timestamp())}"
    payments_col.insert_one({
        "_id": order_id,
        "user_id": user_id,
        "plan_name": plan_name,
        "amount": amount,
        "status": "pending",
        "created_at": now,
        "paid_at": None,
        "premium_until": None,
    })
    return order_id

def mark_payment_paid(order_id: str, minutes_premium: int):
    """Mark payment as paid and extend premium."""
    pay = payments_col.find_one({"_id": order_id})
    if not pay:
        return None
    user_id = pay["user_id"]
    now = datetime.utcnow()
    premium_until = now + timedelta(minutes=minutes_premium)
    payments_col.update_one(
        {"_id": order_id},
        {"$set": {"status": "paid", "paid_at": now, "premium_until": premium_until}}
    )
    update_user(user_id, {"is_premium": True, "premium_until": premium_until})
    return premium_until
