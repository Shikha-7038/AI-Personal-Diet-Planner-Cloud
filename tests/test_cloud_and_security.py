import os
import shutil
import tempfile
import unittest

from backend.utils.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.utils.validators import ValidationError, require_email, require_password, validate_profile_fields
from cloud.database_service import LocalDatabase
from cloud.errors import CloudServiceError, DuplicateEmailError
from cloud.storage_service import LocalStorage, safe_filename


class TestSecurity(unittest.TestCase):
    def test_password_hash_roundtrip(self):
        h = hash_password("SuperSecret123")
        self.assertTrue(verify_password("SuperSecret123", h))
        self.assertFalse(verify_password("wrongpassword", h))

    def test_password_hashes_are_salted(self):
        self.assertNotEqual(hash_password("same-password"), hash_password("same-password"))

    def test_jwt_roundtrip_and_tamper_detection(self):
        token = create_access_token("user-123", secret="test-secret", expires_minutes=5)
        self.assertEqual(decode_access_token(token, "test-secret"), "user-123")
        self.assertIsNone(decode_access_token(token, "wrong-secret"))
        self.assertIsNone(decode_access_token(token + "tampered", "test-secret"))

    def test_expired_token_rejected(self):
        token = create_access_token("user-123", secret="s", expires_minutes=-1)
        self.assertIsNone(decode_access_token(token, "s"))


class TestValidators(unittest.TestCase):
    def test_require_email_rejects_bad_format(self):
        with self.assertRaises(ValidationError):
            require_email("not-an-email")
        self.assertEqual(require_email("USER@Example.com"), "user@example.com")

    def test_require_password_length(self):
        with self.assertRaises(ValidationError):
            require_password("short")
        self.assertEqual(require_password("longenough1"), "longenough1")

    def test_profile_field_ranges(self):
        with self.assertRaises(ValidationError):
            validate_profile_fields({"age": 200})
        out = validate_profile_fields({"age": 25, "goal": "fitness", "dietary_preference": "vegan"})
        self.assertEqual(out["age"], 25)

    def test_invalid_goal_rejected(self):
        with self.assertRaises(ValidationError):
            validate_profile_fields({"goal": "cure-disease"})


class TestLocalDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = LocalDatabase(os.path.join(self.tmp, "test.db"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_and_fetch_user(self):
        user = self.db.create_user("Asha", "asha@example.com", "hashed")
        self.assertEqual(self.db.get_user_by_email("ASHA@example.com")["user_id"], user["user_id"])

    def test_duplicate_email_rejected(self):
        self.db.create_user("Asha", "dup@example.com", "hashed")
        with self.assertRaises(DuplicateEmailError):
            self.db.create_user("Other", "dup@example.com", "hashed2")

    def test_update_user_ignores_unknown_fields(self):
        user = self.db.create_user("Asha", "u2@example.com", "hashed")
        updated = self.db.update_user(user["user_id"], {"age": 30, "password_hash": "HACK"})
        self.assertEqual(updated["age"], 30)
        self.assertEqual(updated["password_hash"], "hashed")  # not overwritten - not in USER_FIELDS

    def test_user_isolation_on_plans(self):
        u1 = self.db.create_user("A", "a@example.com", "h")
        u2 = self.db.create_user("B", "b@example.com", "h")
        plan = {"breakfast": {}, "lunch": {}, "snack": {}, "dinner": {}, "nutrition_summary": {"total_calories": 1}}
        created = self.db.create_plan(u1["user_id"], plan)
        self.assertIsNone(self.db.get_plan(u2["user_id"], created["plan_id"]))
        self.assertIsNotNone(self.db.get_plan(u1["user_id"], created["plan_id"]))
        self.assertEqual(self.db.list_plans(u2["user_id"]), [])

    def test_delete_plan_only_by_owner(self):
        u1 = self.db.create_user("A", "aa@example.com", "h")
        u2 = self.db.create_user("B", "bb@example.com", "h")
        plan = {"breakfast": {}, "lunch": {}, "snack": {}, "dinner": {}, "nutrition_summary": {}}
        created = self.db.create_plan(u1["user_id"], plan)
        self.assertFalse(self.db.delete_plan(u2["user_id"], created["plan_id"]))
        self.assertTrue(self.db.delete_plan(u1["user_id"], created["plan_id"]))

    def test_file_records_and_isolation(self):
        u1 = self.db.create_user("A", "f1@example.com", "h")
        u2 = self.db.create_user("B", "f2@example.com", "h")
        rec = self.db.create_file(u1["user_id"], "photo.png", "users/x/photo.png", "image/png", 123, "upload")
        self.assertIsNone(self.db.get_file(u2["user_id"], rec["file_id"]))
        self.assertEqual(len(self.db.list_files(u1["user_id"])), 1)

    def test_ping(self):
        self.assertTrue(self.db.ping())


class TestLocalStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.storage = LocalStorage(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_read_delete_roundtrip(self):
        path = self.storage.save("user-1", "meal.json", b'{"a":1}', "application/json")
        self.assertTrue(path.startswith("users/user-1/"))
        self.assertEqual(self.storage.read(path), b'{"a":1}')
        self.storage.delete(path)
        with self.assertRaises(CloudServiceError):
            self.storage.read(path)

    def test_path_traversal_blocked(self):
        with self.assertRaises(CloudServiceError):
            self.storage._resolve("../../etc/passwd")

    def test_safe_filename_strips_dangerous_chars(self):
        self.assertEqual(safe_filename("../../etc/passwd"), "passwd")
        self.assertEqual(safe_filename("my plan (final)!.pdf"), "my_plan_final.pdf")


if __name__ == "__main__":
    unittest.main()
