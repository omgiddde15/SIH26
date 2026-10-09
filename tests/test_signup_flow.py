"""
Dedicated Regression Tests for LunarReg Sign Up and Authentication Lifecycle.

Verifies:
1. Task 4: Sign Up -> Login
   - Start unauthenticated.
   - Open Sign Up.
   - Create a unique test account.
   - Assert create_user() succeeds.
   - Assert the user exists in the test database.
   - Return to Login.
   - Authenticate using the newly created test account.
   - Assert authentication succeeds.
   - Assert the app reaches the authenticated Overview page.

2. Task 5: Existing email -> Sign Up
   - Attempt registration using an existing email.
   - Assert registration is rejected cleanly.
   - Assert the original password is unchanged.

3. Task 6: Sign Out -> Sign Up -> Login
   - Authenticate as an existing test user.
   - Sign out.
   - Open Sign Up.
   - Create another new test account.
   - Login with that new account.
   - Verify no stale session state from the previous account remains.
"""

import os
import sys
import uuid
import sqlite3
import unittest
from streamlit.testing.v1 import AppTest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_TESTS_DIR)
_APP_DIR = os.path.join(_PROJECT_DIR, "SIH26_Lunar_Registration", "app")
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from auth import create_user, verify_password, DB_PATH

_APP_PATH = os.path.join(_APP_DIR, "app.py")


class TestSignUpFlow(unittest.TestCase):
    APP_PATH = _APP_PATH

    def test_signup_to_login(self):
        """Task 4: Sign Up -> Login."""
        # 1. Start unauthenticated
        at = AppTest.from_file(self.APP_PATH, default_timeout=30).run()
        self.assertFalse(at.exception, f"Exceptions on unauthenticated run: {at.exception}")
        is_authed = at.session_state["auth_authenticated"] if "auth_authenticated" in at.session_state else False
        self.assertFalse(is_authed, "Initial session must be unauthenticated")

        # 2. Open Sign Up & create a unique test account
        unique_suffix = uuid.uuid4().hex[:8]
        test_email = f"scientist_{unique_suffix}@isro.gov.in"
        test_name = f"Dr. Scientist {unique_suffix}"
        test_password = f"Chandrayaan_{unique_suffix}!"

        at.text_input(key="auth_signup_name").input(test_name)
        at.text_input(key="auth_signup_email").input(test_email)
        at.text_input(key="auth_signup_password").input(test_password)
        at.text_input(key="auth_signup_confirm").input(test_password)

        create_btn = [b for b in at.button if "Create Account" in b.label][0]
        at = create_btn.click().run()
        self.assertFalse(at.exception, f"Exceptions on sign up submit: {at.exception}")

        # 3. Assert create_user() succeeds via UI success toast/message
        success_msgs = [s.value for s in at.success]
        self.assertTrue(len(success_msgs) > 0, "Expected a success message upon account creation")
        self.assertTrue(
            any("Account created successfully" in m for m in success_msgs),
            f"Success message should confirm creation: {success_msgs}",
        )

        # 4. Assert the user exists in the test database
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, full_name, email, password_hash FROM users WHERE email = ?",
                (test_email.lower(),),
            ).fetchone()

        self.assertIsNotNone(row, f"User {test_email} must exist in the database")
        self.assertEqual(row["full_name"], test_name)
        self.assertEqual(row["email"], test_email.lower())
        self.assertTrue(verify_password(test_password, row["password_hash"]), "Password hash in DB must verify")

        # 5. Return to Login and authenticate using the newly created test account
        at.text_input(key="auth_login_email").input(test_email)
        at.text_input(key="auth_login_password").input(test_password)

        login_btn = [b for b in at.button if "Sign In" in b.label][0]
        at = login_btn.click().run()
        self.assertFalse(at.exception, f"Exceptions on login: {at.exception}")

        # 6. Assert authentication succeeds
        self.assertTrue(
            at.session_state.get("auth_authenticated", False)
            if hasattr(at.session_state, "get")
            else at.session_state["auth_authenticated"],
            "User must be authenticated in session_state",
        )
        self.assertEqual(at.session_state["auth_email"], test_email.lower())

        # 7. Assert the app reaches the authenticated Overview page
        nav_page = at.session_state["nav_page"] if "nav_page" in at.session_state else "overview"
        self.assertEqual(nav_page, "overview", "App must reach Overview page upon login")
        logout_buttons = [b for b in at.sidebar.button if b.key == "sidebar_logout_btn"]
        self.assertEqual(len(logout_buttons), 1, "Sidebar Sign out button must be present on Overview page")

    def test_existing_email_signup_rejected(self):
        """Task 5: Existing email -> Sign Up."""
        # 1. Prepare an existing user account in DB
        unique_suffix = uuid.uuid4().hex[:8]
        existing_email = f"existing_{unique_suffix}@isro.gov.in"
        orig_name = f"Original Operator {unique_suffix}"
        orig_password = f"OrigPassword_{unique_suffix}!"
        ok, msg = create_user(orig_name, existing_email, orig_password)
        self.assertTrue(ok, f"Failed to pre-create user: {msg}")

        # Fetch original password hash
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            orig_row = conn.execute(
                "SELECT password_hash FROM users WHERE email = ?",
                (existing_email.lower(),),
            ).fetchone()
        self.assertIsNotNone(orig_row)
        orig_hash = orig_row["password_hash"]

        # 2. Attempt registration using the existing email in UI
        at = AppTest.from_file(self.APP_PATH, default_timeout=30).run()
        at.text_input(key="auth_signup_name").input("Impostor Account")
        at.text_input(key="auth_signup_email").input(existing_email)
        at.text_input(key="auth_signup_password").input("AttemptedNewPass999!")
        at.text_input(key="auth_signup_confirm").input("AttemptedNewPass999!")

        create_btn = [b for b in at.button if "Create Account" in b.label][0]
        at = create_btn.click().run()
        self.assertFalse(at.exception, f"Exceptions on duplicate sign up attempt: {at.exception}")

        # 3. Assert registration is rejected cleanly
        error_msgs = [e.value for e in at.error]
        self.assertTrue(len(error_msgs) > 0, "Expected an error message when signing up with existing email")
        self.assertTrue(
            any("already exists" in m.lower() for m in error_msgs),
            f"Error message should mention existing account: {error_msgs}",
        )
        is_authed = at.session_state["auth_authenticated"] if "auth_authenticated" in at.session_state else False
        self.assertFalse(is_authed, "Duplicate registration must not authenticate the user")

        # 4. Assert the original password is unchanged in the database
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            check_row = conn.execute(
                "SELECT full_name, password_hash FROM users WHERE email = ?",
                (existing_email.lower(),),
            ).fetchone()

        self.assertEqual(check_row["full_name"], orig_name, "User name must remain unchanged")
        self.assertEqual(check_row["password_hash"], orig_hash, "Password hash must remain unchanged")
        self.assertTrue(
            verify_password(orig_password, check_row["password_hash"]),
            "Original password must still verify against the stored hash",
        )
        self.assertFalse(
            verify_password("AttemptedNewPass999!", check_row["password_hash"]),
            "Attempted new password must NOT verify against stored hash",
        )

    def test_sign_out_then_signup_then_login_no_stale_state(self):
        """Task 6: Sign Out -> Sign Up -> Login."""
        # 1. Create and authenticate as an existing test user (User 1)
        unique1 = uuid.uuid4().hex[:8]
        user1_email = f"user1_{unique1}@isro.gov.in"
        user1_name = f"Operator One {unique1}"
        user1_pass = f"User1Pass_{unique1}!"
        ok, msg = create_user(user1_name, user1_email, user1_pass)
        self.assertTrue(ok)

        at = AppTest.from_file(self.APP_PATH, default_timeout=30).run()
        at.text_input(key="auth_login_email").input(user1_email)
        at.text_input(key="auth_login_password").input(user1_pass)
        login_btn = [b for b in at.button if "Sign In" in b.label][0]
        at = login_btn.click().run()

        # Populate user 1 session with sensitive/stale data
        at.session_state["registration_result"] = {"rmse": 0.38, "inliers": 190}
        at.session_state["operator_private_notes"] = "Confidential telemetry from Operator 1"
        at.session_state["export_package"] = {"zip": b"data"}

        # 2. Sign Out
        logout_btn = [b for b in at.sidebar.button if b.key == "sidebar_logout_btn"][0]
        at = logout_btn.click().run()

        is_authed = at.session_state["auth_authenticated"] if "auth_authenticated" in at.session_state else False
        self.assertFalse(is_authed, "Session must be unauthenticated after sign out")

        # 3. Open Sign Up & create another new test account (User 2)
        unique2 = uuid.uuid4().hex[:8]
        user2_email = f"user2_{unique2}@isro.gov.in"
        user2_name = f"Operator Two {unique2}"
        user2_pass = f"User2Pass_{unique2}!"

        at.text_input(key="auth_signup_name").input(user2_name)
        at.text_input(key="auth_signup_email").input(user2_email)
        at.text_input(key="auth_signup_password").input(user2_pass)
        at.text_input(key="auth_signup_confirm").input(user2_pass)

        create_btn = [b for b in at.button if "Create Account" in b.label][0]
        at = create_btn.click().run()
        self.assertFalse(at.exception)
        success_msgs = [s.value for s in at.success]
        self.assertTrue(any("Account created successfully" in m for m in success_msgs))

        # 4. Login with that new account (User 2)
        at.text_input(key="auth_login_email").input(user2_email)
        at.text_input(key="auth_login_password").input(user2_pass)
        login_btn = [b for b in at.button if "Sign In" in b.label][0]
        at = login_btn.click().run()
        self.assertFalse(at.exception)

        # 5. Verify no stale session state from the previous account remains
        self.assertTrue(
            at.session_state["auth_authenticated"],
            "User 2 must be authenticated",
        )
        self.assertEqual(at.session_state["auth_email"], user2_email.lower())
        self.assertEqual(at.session_state["auth_name"], user2_name)
        self.assertNotIn(
            "registration_result",
            at.session_state,
            "registration_result from User 1 must not leak into User 2 session",
        )
        self.assertNotIn(
            "operator_private_notes",
            at.session_state,
            "Private notes from User 1 must not leak into User 2 session",
        )
        self.assertNotIn(
            "export_package",
            at.session_state,
            "export_package from User 1 must not leak into User 2 session",
        )
        nav_page = at.session_state["nav_page"] if "nav_page" in at.session_state else "overview"
        self.assertEqual(nav_page, "overview", "User 2 should land on overview page")


if __name__ == "__main__":
    unittest.main()
