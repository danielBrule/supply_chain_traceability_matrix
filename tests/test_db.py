import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import db


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.path_patch = patch.object(db, "DB_PATH", self.db_path)
        self.path_patch.start()
        db.init_db()

    def tearDown(self):
        self.path_patch.stop()
        self.temp_dir.cleanup()

    def test_category_and_answer_round_trip(self):
        category_id = db.create_category("Metals", "Critical inputs")
        db.save_answer(category_id, "risk", 7)
        self.assertEqual(db.get_answers(category_id), {"risk": 7})
        self.assertEqual(db.get_active_categories()[0]["name"], "Metals")

    def test_saving_answer_updates_category_timestamp(self):
        category_id = db.create_category("Metals")
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("UPDATE categories SET updated_at = '2000-01-01T00:00:00+00:00' WHERE id = ?", (category_id,))
            connection.commit()
        finally:
            connection.close()
        db.save_answer(category_id, "risk", 4)
        self.assertNotEqual(db.get_active_categories()[0]["updated_at"], "2000-01-01T00:00:00+00:00")

    def test_deactivate_and_reactivate(self):
        category_id = db.create_category("Metals")
        db.deactivate_category(category_id)
        self.assertEqual(len(db.get_inactive_categories()), 1)
        db.reactivate_category(category_id)
        self.assertEqual(len(db.get_active_categories()), 1)

    def test_settings_round_trip(self):
        db.save_setting("scenario_id", "socle")
        self.assertEqual(db.get_setting("scenario_id"), "socle")


if __name__ == "__main__":
    unittest.main()
