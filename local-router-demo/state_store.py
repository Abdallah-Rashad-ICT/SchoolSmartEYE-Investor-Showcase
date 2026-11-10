"""SQLite-backed demo node registry and durable request replay guard."""
import json
import os
import sqlite3
import time


class SQLiteStateStore:
    def __init__(self, path=None):
        self.path = path or os.environ.get("SSE_STATE_DB", "schoolsmarteye-demo-state.sqlite3")
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    last_seen REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS accepted_requests (
                    request_id TEXT PRIMARY KEY,
                    accepted_at REAL NOT NULL
                )
            """)

    def register_node(self, node_id, url, capabilities):
        with self._connect() as db:
            db.execute(
                """INSERT INTO nodes(node_id,url,capabilities_json,last_seen)
                   VALUES(?,?,?,?)
                   ON CONFLICT(node_id) DO UPDATE SET
                     url=excluded.url,
                     capabilities_json=excluded.capabilities_json,
                     last_seen=excluded.last_seen""",
                (node_id, url, json.dumps(capabilities), time.time()),
            )

    def list_nodes(self):
        with self._connect() as db:
            rows = db.execute(
                "SELECT node_id,url,capabilities_json,last_seen FROM nodes ORDER BY node_id"
            ).fetchall()
        return [
            {"node_id": row[0], "url": row[1],
             "capabilities": json.loads(row[2]), "last_seen": row[3]}
            for row in rows
        ]

    def claim_request(self, request_id):
        """Atomically accept an ID once; returns False for every replay."""
        try:
            with self._connect() as db:
                db.execute(
                    "INSERT INTO accepted_requests(request_id,accepted_at) VALUES(?,?)",
                    (request_id, time.time()),
                )
            return True
        except sqlite3.IntegrityError:
            return False
