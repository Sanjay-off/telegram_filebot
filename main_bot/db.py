from pymongo import MongoClient
from datetime import datetime, timedelta
from .config import MONGO_URL

# ----------------------------------------------------
# Connect to MongoDB
# ----------------------------------------------------
client = MongoClient(MONGO_URL)
db = client["telegram_filebot"]  # database name

# Collections
users_col = db["users"]
payments_col = db["payments"]
settings_col = db["settings"]

# ----------------------------------------------------
# Default global settings (can be modified by admins)
# ----------------------------------------------------
DEFAULT_SETTINGS = {
    "verify_link": "https://t.me/yourchannel/123",   # How to verify video or guide
    "delete_time_minutes": 10,                       # Auto delete ZIP after X minutes
    "verification_days": 1,                          # Verification validity in days
    "free_downloads": 3,                             # Downloads allowed after verification
    "zip_password": "Legalstuff321",                 # Password shown to user (copyable)
    "premium_minutes": 1440,                         # 1 day premium (default)
}

# ----------------------------------------------------
# USER FUNCTIONS
# ----------------------------------------------------

def get_user(user_id: int) -> dict:
    """
    Returns user document.
    Creates one if not found.
    """
    user = users_col.find_one({"_id": user_id})
    if not user:
        user = {
            "_id": user_id,
            "is_verified": False,
            "verified_until": None,
            "downloads_left": 0,
            "is_premium": False,
            "premium_until": None,
            "last_file_code": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        users_col.insert_one(user)
    return user


def update_user(user_id: int, data: dict):
    """
    Updates a user with provided key/value pairs.
    """
    data["updated_at"] = datetime.utcnow()
    users_col.update_one({"_id": user_id}, {"$set": data}, upsert=True)

# ----------------------------------------------------
# SETTINGS FUNCTIONS
# ----------------------------------------------------

def get_settings() -> dict:
    """
    Returns global settings.
    Merges saved settings with DEFAULT_SETTINGS.
    """
    doc = settings_col.find_one({"_id": "global"})
    if not doc:
        doc = {"_id": "global", **DEFAULT_SETTINGS}
        settings_col.insert_one(doc)

    final_settings = dict(DEFAULT_SETTINGS)
    for key, value in doc.items():
        if key != "_id":
            final_settings[key] = value

    return final_settings


def set_setting(key: str, value):
    """
    Updates a specific setting.
    """
    settings_col.update_one(
        {"_id": "global"},
        {"$set": {key: value}},
        upsert=True
    )

# ----------------------------------------------------
# STATISTICS
# ----------------------------------------------------

def count_users():
    total = users_col.count_documents({})
    verified = users_col.count_documents({"is_verified": True})
    premium = users_col.count_documents({"is_premium": True})
    return total, verified, premium

# ----------------------------------------------------
# PAYMENT FUNCTIONS (SKELETON)
# ----------------------------------------------------

def create_payment(user_id: int, plan_name: str, amount: int) -> str:
    """
    Create a pending payment order.
    Returns an order_id.
    """
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
    """
    Marks payment as paid.
    Extends user's premium.
    Returns new premium_until.
    """
    payment = payments_col.find_one({"_id": order_id})
    if not payment:
        return None

    user_id = payment["user_id"]
    now = datetime.utcnow()
    premium_until = now + timedelta(minutes=minutes_premium)

    # Update payment
    payments_col.update_one(
        {"_id": order_id},
        {"$set": {
            "status": "paid",
            "paid_at": now,
            "premium_until": premium_until
        }}
    )

    # Update user
    update_user(user_id, {
        "is_premium": True,
        "premium_until": premium_until
    })

    return premium_until
