"""At-least-once message handling with an atomic inbox and side effect."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    message_id: str
    account_id: str
    amount_cents: int


class Consumer:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS account_totals (
                account_id TEXT PRIMARY KEY,
                total_cents INTEGER NOT NULL
            );
            """
        )

    def handle(self, message: Message) -> bool:
        if message.amount_cents < 0:
            raise ValueError("negative amount is invalid")
        try:
            with self.db:
                inserted = self.db.execute(
                    "INSERT OR IGNORE INTO processed_messages(message_id) VALUES (?)",
                    (message.message_id,),
                ).rowcount
                if inserted == 0:
                    return False  # duplicate: acknowledge without side effect
                self.db.execute(
                    """
                    INSERT INTO account_totals(account_id, total_cents) VALUES (?, ?)
                    ON CONFLICT(account_id) DO UPDATE SET total_cents = total_cents + excluded.total_cents
                    """,
                    (message.account_id, message.amount_cents),
                )
            return True
        except Exception:
            # The transaction is rolled back; broker code must not acknowledge.
            raise


if __name__ == "__main__":
    consumer = Consumer(sqlite3.connect(":memory:"))
    message = Message("evt-001", "acct-7", 2500)
    print("first delivery:", consumer.handle(message))
    print("replay:", consumer.handle(message))
    print(consumer.db.execute("SELECT * FROM account_totals").fetchall())
