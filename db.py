"""
MongoDB helper — সব data এখানে save/load হবে।
Render-এ MONGO_URI environment variable set করতে হবে।
"""

import os
import json
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "")

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client["otp_bot"]
    return _db

# ─── users_data ──────────────────────────────────────────────
def load_users() -> dict:
    db = get_db()
    doc = db["users_data"].find_one({"_id": "data"})
    if doc:
        return doc.get("users", {}), doc.get("active_numbers", {})
    return {}, {}

def save_users(users_data: dict, active_numbers: dict):
    db = get_db()
    db["users_data"].replace_one(
        {"_id": "data"},
        {"_id": "data", "users": users_data, "active_numbers": active_numbers},
        upsert=True
    )

# ─── numbers_db ──────────────────────────────────────────────
def load_numbers() -> dict:
    db = get_db()
    doc = db["numbers_db"].find_one({"_id": "data"})
    return doc.get("numbers", {}) if doc else {}

def save_numbers(numbers_db: dict):
    db = get_db()
    db["numbers_db"].replace_one(
        {"_id": "data"},
        {"_id": "data", "numbers": numbers_db},
        upsert=True
    )

# ─── used_stats ──────────────────────────────────────────────
def load_used_stats() -> dict:
    db = get_db()
    doc = db["used_stats"].find_one({"_id": "data"})
    return doc.get("stats", {}) if doc else {}

def save_used_stats(used_stats: dict):
    db = get_db()
    db["used_stats"].replace_one(
        {"_id": "data"},
        {"_id": "data", "stats": used_stats},
        upsert=True
    )

# ─── seen_ids (otp_monitor এর জন্য) ─────────────────────────
def load_seen() -> set:
    db = get_db()
    doc = db["seen_ids"].find_one({"_id": "data"})
    return set(doc.get("ids", [])) if doc else set()

def save_seen(seen_set: set):
    seen_list = list(seen_set)[-2000:]  # শুধু শেষ 2000টা রাখো
    db = get_db()
    db["seen_ids"].replace_one(
        {"_id": "data"},
        {"_id": "data", "ids": seen_list},
        upsert=True
    )
