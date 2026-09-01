import os
import hmac
import hashlib
import json
import time
import sqlite3
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB = os.getenv("DATABASE_PATH", "rewardrush.db")

app = FastAPI(title="RewardRush Mini App")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance INTEGER DEFAULT 0,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        created_at INTEGER,
        last_daily_at INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        amount INTEGER,
        method TEXT,
        destination TEXT,
        status TEXT DEFAULT 'pending',
        created_at INTEGER
    );
    """)

    conn.commit()
    conn.close()


init_db()


def validate_telegram_data(init_data):
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN is not configured"
        )

    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram initData"
        )

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram hash"
        )

    check_string = "\n".join(
        f"{key}={data[key]}"
        for key in sorted(data)
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram data"
        )

    try:
        return json.loads(data["user"])
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram user"
        )


async def get_current_user(request: Request):
    init_data = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    return validate_telegram_data(init_data)


def create_user(user):
    telegram_id = int(user["id"])
    now = int(time.time())

    conn = get_db()

    existing = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    ).fetchone()

    if not existing:
        referral_code = f"rr{telegram_id}"

        conn.execute(
            """
            INSERT INTO users
            (
                telegram_id,
                username,
                first_name,
                balance,
                referral_code,
                created_at
            )
            VALUES (?, ?, ?, 0, ?, ?)
            """,
            (
                telegram_id,
                user.get("username", ""),
                user.get("first_name", ""),
                referral_code,
                now
            )
        )

        conn.commit()

    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    ).fetchone()

    conn.close()

    return row


@app.get("/")
async def home():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "RewardRush"
    }


@app.get("/api/me")
async def me(request: Request):

    user = await get_current_user(request)
    row = create_user(user)

    return {
        "id": row["telegram_id"],
        "username": row["username"],
        "first_name": row["first_name"],
        "balance": row["balance"],
        "referral_code": row["referral_code"]
    }


@app.post("/api/daily")
async def daily(request: Request):

    user = await get_current_user(request)
    row = create_user(user)

    now = int(time.time())

    if now - row["last_daily_at"] < 86400:

        remaining = 86400 - (
            now - row["last_daily_at"]
        )

        return {
            "ok": False,
            "message": "Daily reward already claimed.",
            "remaining": remaining
        }

    reward = 100

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET balance = balance + ?,
            last_daily_at = ?
        WHERE telegram_id = ?
        """,
        (
            reward,
            now,
            int(user["id"])
        )
    )

    conn.commit()

    new_balance = conn.execute(
        "SELECT balance FROM users WHERE telegram_id = ?",
        (int(user["id"]),)
    ).fetchone()["balance"]

    conn.close()

    return {
        "ok": True,
        "reward": reward,
        "balance": new_balance
    }


@app.get("/api/leaderboard")
async def leaderboard(request: Request):

    await get_current_user(request)

    conn = get_db()

    rows = conn.execute(
        """
        SELECT first_name, username, balance
        FROM users
        ORDER BY balance DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    return {
        "items": [dict(row) for row in rows]
    }


class WithdrawRequest(BaseModel):
    amount: int
    method: str
    destination: str


@app.post("/api/withdraw")
async def withdraw(
    payload: WithdrawRequest,
    request: Request
):

    user = await get_current_user(request)
    create_user(user)

    if payload.amount < 10000:
        raise HTTPException(
            status_code=400,
            detail="Minimum withdrawal is 10,000 points."
        )

    if not payload.destination.strip():
        raise HTTPException(
            status_code=400,
            detail="Destination is required."
        )

    telegram_id = int(user["id"])

    conn = get_db()

    row = conn.execute(
        "SELECT balance FROM users WHERE telegram_id = ?",
        (telegram_id,)
    ).fetchone()

    if row["balance"] < payload.amount:
        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Insufficient balance."
        )

    conn.execute(
        """
        UPDATE users
        SET balance = balance - ?
        WHERE telegram_id = ?
        """,
        (
            payload.amount,
            telegram_id
        )
    )

    conn.execute(
        """
        INSERT INTO withdrawals
        (
            telegram_id,
            amount,
            method,
            destination,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (
            telegram_id,
            payload.amount,
            payload.method,
            payload.destination,
            int(time.time())
        )
    )

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "message": "Withdrawal request submitted."
    }
