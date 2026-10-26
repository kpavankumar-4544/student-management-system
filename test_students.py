"""
Automated tests for the Student Management System.

Run with:   python -m unittest test_students -v
"""

import os
import tempfile
import unittest

# Point the app at a throw-away database BEFORE importing it
_TMP_DIR = tempfile.mkdtemp()
os.environ["STUDENT_DB_PATH"] = os.path.join(_TMP_DIR, "test.db")

import app  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        app.DB_FILE = os.path.join(_TMP_DIR, f"{self.id()}.db")
        app.init_db()

    def _add(self, roll="CS101", name="Asha Rao"):
        return app.add_student(name, roll, "CSE", "2nd Year", "asha@college.edu", "9876543210")

    def test_table_created_automatically(self):
        self.assertTrue(app.get_all_students().empty)

    def test_add_student(self):
        ok, _ = self._add()
        self.assertTrue(ok)
        self.assertEqual(len(app.get_all_students()), 1)

    def test_duplicate_roll_rejected(self):
        self._add("CS101")
        ok, msg = self._add("CS101", "Someone Else")
        self.assertFalse(ok)
        self.assertIn("already exists", msg)
        self.assertEqual(len(app.get_all_students()), 1)

    def test_duplicate_roll_rejected_case_insensitive(self):
        self._add("CS101")
        ok, _ = self._add("cs101", "Other")
        self.assertFalse(ok)

    def test_search_by_name_and_roll(self):
        self._add("CS101", "Asha Rao")
        self._add("EC202", "Ravi Kumar")
        self.assertEqual(len(app.search_students("asha")), 1)
        self.assertEqual(len(app.search_students("EC2")), 1)
        self.assertTrue(app.search_students("zzz").empty)

    def test_search_is_safe_against_sql_injection(self):
        self._add()
        self.assertTrue(app.search_students("' OR '1'='1").empty)
        self.assertEqual(len(app.get_all_students()), 1)

    def test_update_student(self):
        self._add()
        sid = int(app.get_all_students().iloc[0]["id"])
        ok, _ = app.update_student(sid, "Asha R", "CS101", "IT", "3rd Year", "a@b.com", "9999999999")
        self.assertTrue(ok)
        student = app.get_student_by_id(sid)
        self.assertEqual(student["name"], "Asha R")
        self.assertEqual(student["department"], "IT")

    def test_update_to_duplicate_roll_rejected(self):
        self._add("CS101")
        self._add("CS102", "Other")
        sid = int(app.get_student_by_id(2)["id"])
        ok, _ = app.update_student(sid, "Other", "CS101", "CSE", "1st Year", "o@b.com", "9999999999")
        self.assertFalse(ok)

    def test_delete_student(self):
        self._add()
        sid = int(app.get_all_students().iloc[0]["id"])
        ok, _ = app.delete_student(sid)
        self.assertTrue(ok)
        self.assertTrue(app.get_all_students().empty)
        ok, _ = app.delete_student(sid)  # already gone
        self.assertFalse(ok)

    def test_department_counts(self):
        self._add("CS101")
        self._add("CS102", "B")
        app.add_student("C", "EC1", "ECE", "1st Year", "c@d.com", "9999999999")
        self.assertEqual(dict(app.count_by_department()), {"CSE": 2, "ECE": 1})

    def test_csv_export_content(self):
        self._add()
        csv = app.to_display_table(app.get_all_students()).to_csv(index=False)
        self.assertIn("Student Name,Roll Number,Department", csv)
        self.assertIn("Asha Rao,CS101,CSE", csv)


class ValidationTests(unittest.TestCase):
    def test_valid_input(self):
        self.assertEqual(app.validate_student("Asha Rao", "CS101", "a@b.com", "9876543210"), [])

    def test_empty_inputs(self):
        self.assertEqual(len(app.validate_student("", "", "", "")), 4)

    def test_invalid_email_phone_name(self):
        self.assertTrue(app.validate_student("Asha", "CS1", "not-an-email", "9876543210"))
        self.assertTrue(app.validate_student("Asha", "CS1", "a@b.com", "12345"))
        self.assertTrue(app.validate_student("Asha", "CS1", "a@b.com", "98765abcde"))
        self.assertTrue(app.validate_student("12345", "CS1", "a@b.com", "9876543210"))
        self.assertTrue(app.validate_student("Asha", "CS 1;--", "a@b.com", "9876543210"))

    def test_clean_inputs(self):
        self.assertEqual(
            app.clean_inputs("  Asha   Rao ", " cs101 ", " A@B.com ", "98765 43210"),
            ("Asha Rao", "CS101", "a@b.com", "9876543210"),
        )


class UITests(unittest.TestCase):
    """Drive the real Streamlit pages with Streamlit's AppTest helper."""

    def setUp(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ImportError:  # very old Streamlit
            self.skipTest("Streamlit AppTest not available")
        os.environ["STUDENT_DB_PATH"] = os.path.join(_TMP_DIR, f"ui_{self.id()}.db")
        app.DB_FILE = os.environ["STUDENT_DB_PATH"]  # lets tests inspect the same DB
        self.at = AppTest.from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"), default_timeout=30).run()

    def _go(self, page):
        self.at.sidebar.radio[0].set_value(page).run()

    def _field(self, label_start):
        """Find a text box by the start of its label (order on screen != order in code)."""
        return next(t for t in self.at.text_input if t.label.startswith(label_start))

    def _fill_add_form(self, name, roll, email, phone):
        self._field("Student Name").set_value(name)
        self._field("Roll Number").set_value(roll)
        self._field("Email").set_value(email)
        self._field("Phone").set_value(phone)
        self.at.button[0].click().run()

    def test_dashboard_loads_with_no_errors(self):
        self.assertFalse(self.at.exception)

    def test_add_valid_then_duplicate_and_invalid(self):
        self._go("➕ Add Student")
        self._fill_add_form("Asha Rao", "CS101", "asha@college.edu", "9876543210")
        self.assertFalse(self.at.exception)
        self.assertEqual(len(self.at.success), 1)

        self._fill_add_form("Other", "cs101", "o@college.edu", "9876543210")
        self.assertTrue(any("already exists" in e.value for e in self.at.error))

        self._fill_add_form("", "", "bad", "123")
        self.assertGreaterEqual(len(self.at.error), 4)

    def test_search_page_messages(self):
        self._go("➕ Add Student")
        self._fill_add_form("Asha Rao", "CS101", "asha@college.edu", "9876543210")
        self._go("🔍 Search Student")
        self.at.text_input[0].set_value("asha").run()
        self.assertEqual(len(self.at.success), 1)
        self.at.text_input[0].set_value("nobody").run()
        self.assertEqual(len(self.at.warning), 1)

    def test_delete_requires_confirmation(self):
        self._go("➕ Add Student")
        self._fill_add_form("Asha Rao", "CS101", "asha@college.edu", "9876543210")
        self._go("🗑️ Delete Student")
        self.at.button[0].click().run()          # no confirmation ticked
        self.assertTrue(any("confirmation" in e.value for e in self.at.error))
        self.at.checkbox[0].check().run()
        self.at.button[0].click().run()
        self.assertEqual(len(self.at.success), 1)

    def test_update_page_saves_changes(self):
        self._go("➕ Add Student")
        self._fill_add_form("Asha Rao", "CS101", "asha@college.edu", "9876543210")
        self._go("✏️ Update Student")
        self._field("Student Name").set_value("Asha R. Rao")
        self.at.button[0].click().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(len(self.at.success), 1)
        self.assertEqual(app.get_student_by_id(1)["name"], "Asha R. Rao")

    def test_update_page_rejects_invalid_email(self):
        self._go("➕ Add Student")
        self._fill_add_form("Asha Rao", "CS101", "asha@college.edu", "9876543210")
        self._go("✏️ Update Student")
        self._field("Email").set_value("broken")
        self.at.button[0].click().run()
        self.assertTrue(any("valid email" in e.value for e in self.at.error))

    def test_view_page_shows_table_and_filter(self):
        self._go("➕ Add Student")
        self._fill_add_form("Asha Rao", "CS101", "asha@college.edu", "9876543210")
        self._go("📋 View Students")
        self.assertFalse(self.at.exception)
        self.assertEqual(len(self.at.dataframe), 1)
        self.at.text_input[0].set_value("nomatch").run()
        self.assertEqual(len(self.at.warning), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
