"""
Cloud database layer.

`DatabaseService` is the interface the backend talks to. Two implementations:
  * LocalDatabase      - SQLite file. Free, offline, perfect for local "cloud simulation".
  * FirestoreDatabase  - Google Firebase Firestore (free Spark tier). Real managed cloud DB.
Switch with the DB_BACKEND environment variable. Backend code never changes.

USER ISOLATION: every plan/file query requires user_id, so one user can never read
another user's rows through the API (the data layer enforces it, not only the routes).
"""
import hashlib
import json
import os
import sqlite3
import uuid
from abc import ABC, abstractmethod
from contextlib import closing
from datetime import datetime, timezone
from typing import Optional

from cloud.errors import CloudServiceError, DuplicateEmailError

USER_FIELDS = {"name", "sex", "age", "height", "weight", "activity_level",
               "dietary_preference", "goal", "allergies", "preferences", "updated_at"}
PLAN_MEALS = ("breakfast", "lunch", "snack", "dinner")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid.uuid4().hex


class DatabaseService(ABC):
    # ---- USERS ----
    @abstractmethod
    def create_user(self, name: str, email: str, password_hash: str) -> dict: ...
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[dict]: ...
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[dict]: ...
    @abstractmethod
    def update_user(self, user_id: str, fields: dict) -> Optional[dict]: ...
    # ---- DIET_PLANS ----
    @abstractmethod
    def create_plan(self, user_id: str, plan: dict) -> dict: ...
    @abstractmethod
    def list_plans(self, user_id: str) -> list: ...
    @abstractmethod
    def get_plan(self, user_id: str, plan_id: str) -> Optional[dict]: ...
    @abstractmethod
    def update_plan(self, user_id: str, plan_id: str, fields: dict) -> Optional[dict]: ...
    @abstractmethod
    def delete_plan(self, user_id: str, plan_id: str) -> bool: ...
    # ---- USER_FILES ----
    @abstractmethod
    def create_file(self, user_id: str, filename: str, storage_path: str, content_type: str,
                    size_bytes: int, kind: str) -> dict: ...
    @abstractmethod
    def list_files(self, user_id: str) -> list: ...
    @abstractmethod
    def get_file(self, user_id: str, file_id: str) -> Optional[dict]: ...
    @abstractmethod
    def delete_file(self, user_id: str, file_id: str) -> bool: ...
    @abstractmethod
    def ping(self) -> bool: ...


# ----------------------------------------------------------------------------------------
# SQLite implementation (local simulation of a cloud database)
# ----------------------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, sex TEXT, age INTEGER, height REAL, weight REAL,
    activity_level TEXT, dietary_preference TEXT, goal TEXT,
    allergies TEXT DEFAULT '[]', preferences TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS diet_plans (
    plan_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    breakfast TEXT, lunch TEXT, snack TEXT, dinner TEXT, nutrition_summary TEXT,
    extra TEXT DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_files (
    file_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    filename TEXT NOT NULL, storage_path TEXT NOT NULL, content_type TEXT, size_bytes INTEGER,
    kind TEXT DEFAULT 'upload', uploaded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_plans_user ON diet_plans(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_files_user ON user_files(user_id, uploaded_at);
"""


class LocalDatabase(DatabaseService):
    def __init__(self, path: str):
        self.path = path
        folder = os.path.dirname(os.path.abspath(path))
        os.makedirs(folder, exist_ok=True)
        try:
            with closing(self._conn()) as conn, conn:
                conn.executescript(SCHEMA)
        except sqlite3.Error as exc:
            raise CloudServiceError("Could not initialise local database") from exc

    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _run(self, sql, params=(), fetch=None):
        """Execute one statement inside a transaction; wrap DB errors as CloudServiceError."""
        try:
            with closing(self._conn()) as conn, conn:
                cur = conn.execute(sql, params)
                if fetch == "one":
                    return cur.fetchone()
                if fetch == "all":
                    return cur.fetchall()
                return cur.rowcount
        except sqlite3.IntegrityError:
            raise
        except sqlite3.Error as exc:
            raise CloudServiceError("Database operation failed") from exc

    @staticmethod
    def _user(row) -> Optional[dict]:
        if row is None:
            return None
        d = dict(row)
        d["allergies"] = json.loads(d.get("allergies") or "[]")
        return d

    @staticmethod
    def _plan(row) -> Optional[dict]:
        if row is None:
            return None
        d = dict(row)
        for key in (*PLAN_MEALS, "nutrition_summary"):
            d[key] = json.loads(d[key]) if d.get(key) else None
        d.update(json.loads(d.pop("extra") or "{}"))
        return d

    # ---- users ----
    def create_user(self, name, email, password_hash):
        user_id, ts = new_id(), now_iso()
        try:
            self._run("INSERT INTO users (user_id, name, email, password_hash, created_at, updated_at) "
                      "VALUES (?,?,?,?,?,?)", (user_id, name, email.lower(), password_hash, ts, ts))
        except sqlite3.IntegrityError as exc:
            raise DuplicateEmailError(email) from exc
        return self.get_user_by_id(user_id)

    def get_user_by_email(self, email):
        return self._user(self._run("SELECT * FROM users WHERE email = ?", (email.lower(),), "one"))

    def get_user_by_id(self, user_id):
        return self._user(self._run("SELECT * FROM users WHERE user_id = ?", (user_id,), "one"))

    def update_user(self, user_id, fields):
        fields = {k: v for k, v in fields.items() if k in USER_FIELDS}
        fields["updated_at"] = now_iso()
        if "allergies" in fields:
            fields["allergies"] = json.dumps(fields["allergies"] or [])
        cols = ", ".join(f"{k} = ?" for k in fields)  # keys come from the USER_FIELDS whitelist
        self._run(f"UPDATE users SET {cols} WHERE user_id = ?", (*fields.values(), user_id))
        return self.get_user_by_id(user_id)

    # ---- plans ----
    def create_plan(self, user_id, plan):
        plan_id, ts = new_id(), now_iso()
        meals = [json.dumps(plan[m]) for m in PLAN_MEALS]
        extra = {k: v for k, v in plan.items() if k not in (*PLAN_MEALS, "nutrition_summary")}
        self._run("INSERT INTO diet_plans (plan_id, user_id, breakfast, lunch, snack, dinner, "
                  "nutrition_summary, extra, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                  (plan_id, user_id, *meals, json.dumps(plan["nutrition_summary"]), json.dumps(extra), ts))
        return self.get_plan(user_id, plan_id)

    def list_plans(self, user_id):
        rows = self._run("SELECT * FROM diet_plans WHERE user_id = ? ORDER BY created_at DESC", (user_id,), "all")
        return [self._plan(r) for r in rows]

    def get_plan(self, user_id, plan_id):
        return self._plan(self._run("SELECT * FROM diet_plans WHERE plan_id = ? AND user_id = ?",
                                    (plan_id, user_id), "one"))

    def update_plan(self, user_id, plan_id, fields):
        current = self.get_plan(user_id, plan_id)
        if current is None:
            return None
        extra = {k: v for k, v in current.items()
                 if k not in ("plan_id", "user_id", "created_at", "nutrition_summary", *PLAN_MEALS)}
        extra.update(fields)
        self._run("UPDATE diet_plans SET extra = ? WHERE plan_id = ? AND user_id = ?",
                  (json.dumps(extra), plan_id, user_id))
        return self.get_plan(user_id, plan_id)

    def delete_plan(self, user_id, plan_id):
        return self._run("DELETE FROM diet_plans WHERE plan_id = ? AND user_id = ?", (plan_id, user_id)) > 0

    # ---- files ----
    def create_file(self, user_id, filename, storage_path, content_type, size_bytes, kind):
        file_id, ts = new_id(), now_iso()
        self._run("INSERT INTO user_files (file_id, user_id, filename, storage_path, content_type, size_bytes, "
                  "kind, uploaded_at) VALUES (?,?,?,?,?,?,?,?)",
                  (file_id, user_id, filename, storage_path, content_type, size_bytes, kind, ts))
        return self.get_file(user_id, file_id)

    def list_files(self, user_id):
        rows = self._run("SELECT * FROM user_files WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,), "all")
        return [dict(r) for r in rows]

    def get_file(self, user_id, file_id):
        row = self._run("SELECT * FROM user_files WHERE file_id = ? AND user_id = ?", (file_id, user_id), "one")
        return dict(row) if row else None

    def delete_file(self, user_id, file_id):
        return self._run("DELETE FROM user_files WHERE file_id = ? AND user_id = ?", (file_id, user_id)) > 0

    def ping(self):
        self._run("SELECT 1", fetch="one")
        return True


# ----------------------------------------------------------------------------------------
# Firestore implementation (real managed cloud database, free Spark tier)
# ----------------------------------------------------------------------------------------
class FirestoreDatabase(DatabaseService):
    """Collections: users, user_emails (uniqueness), diet_plans, user_files."""

    def __init__(self, credentials_path=None, storage_bucket=None):
        from cloud.firebase_init import init_firebase
        init_firebase(credentials_path, storage_bucket)
        try:
            from firebase_admin import firestore
            self.db = firestore.client()
        except Exception as exc:  # pragma: no cover
            raise CloudServiceError("Could not connect to Firestore") from exc

    def _guard(self, fn):
        try:
            return fn()
        except (DuplicateEmailError, CloudServiceError):
            raise
        except Exception as exc:  # network, permission, quota ...
            raise CloudServiceError("Firestore operation failed") from exc

    @staticmethod
    def _email_key(email: str) -> str:
        return hashlib.sha256(email.lower().encode()).hexdigest()

    def create_user(self, name, email, password_hash):
        user_id, ts = new_id(), now_iso()

        def op():
            from google.api_core.exceptions import AlreadyExists
            try:  # .create() fails if the document exists -> atomic unique-email check
                self.db.collection("user_emails").document(self._email_key(email)).create({"user_id": user_id})
            except AlreadyExists as exc:
                raise DuplicateEmailError(email) from exc
            doc = {"user_id": user_id, "name": name, "email": email.lower(), "password_hash": password_hash,
                   "sex": None, "age": None, "height": None, "weight": None, "activity_level": None,
                   "dietary_preference": None, "goal": None, "allergies": [], "preferences": "",
                   "created_at": ts, "updated_at": ts}
            self.db.collection("users").document(user_id).set(doc)
            return doc
        return self._guard(op)

    def get_user_by_id(self, user_id):
        snap = self._guard(lambda: self.db.collection("users").document(user_id).get())
        return snap.to_dict() if snap.exists else None

    def get_user_by_email(self, email):
        def op():
            docs = list(self.db.collection("users").where("email", "==", email.lower()).limit(1).stream())
            return docs[0].to_dict() if docs else None
        return self._guard(op)

    def update_user(self, user_id, fields):
        fields = {k: v for k, v in fields.items() if k in USER_FIELDS}
        fields["updated_at"] = now_iso()
        self._guard(lambda: self.db.collection("users").document(user_id).update(fields))
        return self.get_user_by_id(user_id)

    def create_plan(self, user_id, plan):
        plan_id = new_id()
        doc = {**plan, "plan_id": plan_id, "user_id": user_id, "created_at": now_iso()}
        self._guard(lambda: self.db.collection("diet_plans").document(plan_id).set(doc))
        return doc

    def _owned(self, collection, key, user_id, doc_id):
        snap = self.db.collection(collection).document(doc_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        return data if data.get("user_id") == user_id else None  # user isolation

    def list_plans(self, user_id):
        def op():
            docs = self.db.collection("diet_plans").where("user_id", "==", user_id).stream()
            return sorted((d.to_dict() for d in docs), key=lambda d: d["created_at"], reverse=True)
        return self._guard(op)

    def get_plan(self, user_id, plan_id):
        return self._guard(lambda: self._owned("diet_plans", "plan_id", user_id, plan_id))

    def update_plan(self, user_id, plan_id, fields):
        if self.get_plan(user_id, plan_id) is None:
            return None
        self._guard(lambda: self.db.collection("diet_plans").document(plan_id).update(fields))
        return self.get_plan(user_id, plan_id)

    def delete_plan(self, user_id, plan_id):
        if self.get_plan(user_id, plan_id) is None:
            return False
        self._guard(lambda: self.db.collection("diet_plans").document(plan_id).delete())
        return True

    def create_file(self, user_id, filename, storage_path, content_type, size_bytes, kind):
        file_id = new_id()
        doc = {"file_id": file_id, "user_id": user_id, "filename": filename, "storage_path": storage_path,
               "content_type": content_type, "size_bytes": size_bytes, "kind": kind, "uploaded_at": now_iso()}
        self._guard(lambda: self.db.collection("user_files").document(file_id).set(doc))
        return doc

    def list_files(self, user_id):
        def op():
            docs = self.db.collection("user_files").where("user_id", "==", user_id).stream()
            return sorted((d.to_dict() for d in docs), key=lambda d: d["uploaded_at"], reverse=True)
        return self._guard(op)

    def get_file(self, user_id, file_id):
        return self._guard(lambda: self._owned("user_files", "file_id", user_id, file_id))

    def delete_file(self, user_id, file_id):
        if self.get_file(user_id, file_id) is None:
            return False
        self._guard(lambda: self.db.collection("user_files").document(file_id).delete())
        return True

    def ping(self):
        self._guard(lambda: list(self.db.collection("users").limit(1).stream()))
        return True


def build_database(backend, sqlite_path="data/diet_planner.db", credentials_path=None, storage_bucket=None):
    if backend == "supabase":
        from cloud.supabase_service import SupabaseDatabase
        return SupabaseDatabase()
    if backend == "firestore":
        return FirestoreDatabase(credentials_path, storage_bucket)
    return LocalDatabase(sqlite_path)
