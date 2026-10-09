"""
Automated regression test suite for LunarReg Quick Demo Access feature.

Verifies:
1. Unauthenticated -> Quick Demo Access -> authenticated Overview.
2. Quick Demo Access does not require email/password inputs.
3. Normal Login still works.
4. Normal Sign Up still works.
5. Logout from Demo Mode returns to Login without flicker/warning.
6. Quick Demo Access after logout works again.
7. Quick Demo Access does not inherit previous registration/session data.
8. Demo user does not overwrite an existing real account.
9. Verification that 'Calling st.rerun() within a callback is a no-op' is never emitted.
"""

from __future__ import annotations

import os
import sys
import unittest
import sqlite3
from typing import Dict, Any

from streamlit.testing.v1 import AppTest

# Resolve paths dynamically
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_TESTS_DIR)

possible_app_paths = [
    os.path.join(_PROJECT_DIR, "SIH26_Lunar_Registration", "app", "app.py"),
    os.path.join(_PROJECT_DIR, "app", "app.py"),
]
APP_PATH = None
for p in possible_app_paths:
    if os.path.exists(p):
        APP_PATH = p
        break

APP_DIR = os.path.dirname(APP_PATH) if APP_PATH else None
if APP_DIR and APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from auth import (
    init_auth_db,
    create_user,
    authenticate_user,
    is_authenticated,
    set_authenticated,
    logout_user,
    get_or_create_demo_user,
    handle_quick_demo_access,
    is_demo_session,
    DEMO_USER_NAME,
    DEMO_USER_EMAIL,
    DB_PATH,
)


class TestQuickDemoAccess(unittest.TestCase):
    """Regression test suite for SIH Quick Demo Access."""

    @classmethod
    def setUpClass(cls):
        init_auth_db()

    def setUp(self):
        import streamlit as st
        # Clear per-test session state
        for k in list(st.session_state.keys()):
            del st.session_state[k]

    def test_01_unauthenticated_to_quick_demo_access(self):
        """1. Unauthenticated -> Quick Demo Access -> authenticated Overview."""
        import streamlit as st

        self.assertFalse(is_authenticated())

        # Trigger quick demo access callback
        handle_quick_demo_access()

        self.assertTrue(is_authenticated())
        self.assertTrue(is_demo_session())
        self.assertEqual(st.session_state.get("auth_name"), DEMO_USER_NAME)
        self.assertEqual(st.session_state.get("auth_email"), DEMO_USER_EMAIL.lower())
        self.assertTrue(st.session_state.get("auth_is_demo"))
        self.assertEqual(st.session_state.get("nav_page"), "overview")
        self.assertEqual(st.session_state.get("sidebar_page"), "Overview")

    def test_02_quick_demo_access_does_not_require_credentials(self):
        """2. Quick Demo Access requires zero email or password inputs."""
        import streamlit as st

        # Verify no login inputs exist in session state
        self.assertNotIn("auth_login_email", st.session_state)
        self.assertNotIn("auth_login_password", st.session_state)

        # Call with no parameters
        handle_quick_demo_access()

        self.assertTrue(is_authenticated())
        self.assertEqual(st.session_state["auth_email"], DEMO_USER_EMAIL.lower())

    def test_03_normal_login_still_works(self):
        """3. Normal login flow works seamlessly and preserves non-demo role."""
        import uuid
        import streamlit as st

        real_email = f"evaluator_{uuid.uuid4().hex[:8]}@sac.isro.gov.in"
        real_pass = "ComplexPass#2026"
        create_user("Dr. Regular Evaluator", real_email, real_pass)

        auth_res = authenticate_user(real_email, real_pass)
        self.assertIsNotNone(auth_res)
        uid, name, eml = auth_res
        self.assertEqual(name, "Dr. Regular Evaluator")
        self.assertEqual(eml, real_email)

        set_authenticated(uid, name, eml)
        self.assertTrue(is_authenticated())
        self.assertFalse(is_demo_session())
        self.assertFalse(st.session_state.get("auth_is_demo", False))

    def test_04_normal_signup_still_works(self):
        """4. Normal sign-up flow creates new accounts without conflict."""
        import uuid

        new_email = f"scientist_{uuid.uuid4().hex[:8]}@prl.res.in"
        ok, msg = create_user("Prof. New Scientist", new_email, "ScientistPass123")
        self.assertTrue(ok, f"create_user failed: {msg}")
        self.assertIn("Account created successfully", msg)

        # Duplicate email rejection
        dup_ok, dup_msg = create_user("Imposter", new_email, "DifferentPass123")
        self.assertFalse(dup_ok)
        self.assertIn("already exists", dup_msg)

    def test_05_logout_from_demo_mode_returns_to_login(self):
        """5. Logout from Demo Mode returns to Login cleanly."""
        import streamlit as st

        handle_quick_demo_access()
        self.assertTrue(is_authenticated())
        self.assertTrue(is_demo_session())

        # Simulate sign out callback
        logout_user()
        st.session_state["nav_page"] = "login"
        st.session_state["pending_nav_target"] = "login"

        self.assertFalse(is_authenticated())
        self.assertFalse(is_demo_session())
        self.assertNotIn("auth_authenticated", st.session_state)
        self.assertNotIn("auth_email", st.session_state)
        self.assertNotIn("auth_is_demo", st.session_state)
        self.assertEqual(st.session_state["nav_page"], "login")

    def test_06_quick_demo_access_after_logout_works_again(self):
        """6. Quick Demo Access after logout works repeatedly without duplicate errors."""
        import streamlit as st

        # Run 1: Demo access
        handle_quick_demo_access()
        self.assertTrue(is_authenticated())

        # Logout
        logout_user()
        self.assertFalse(is_authenticated())

        # Run 2: Demo access again
        handle_quick_demo_access()
        self.assertTrue(is_authenticated())
        self.assertTrue(is_demo_session())
        self.assertEqual(st.session_state["auth_email"], DEMO_USER_EMAIL.lower())
        self.assertEqual(st.session_state["nav_page"], "overview")

    def test_07_quick_demo_access_does_not_inherit_previous_session_data(self):
        """7. Quick Demo Access strictly purges stale registration/session state."""
        import streamlit as st

        # Seed stale data from a hypothetical prior user session
        st.session_state["registration_result"] = {"H": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "inliers": 250}
        st.session_state["source_img_data"] = "dummy_src_data"
        st.session_state["reference_img_data"] = "dummy_ref_data"
        st.session_state["source_filename"] = "old_src.png"
        st.session_state["reference_filename"] = "old_ref.png"
        st.session_state["source_metadata"] = {"valid": True, "product_identifier": "OLD_001"}
        st.session_state["reference_metadata"] = {"valid": True, "product_identifier": "OLD_002"}
        st.session_state["homography"] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        st.session_state["validation_results"] = {"ncc": 0.98}
        st.session_state["export_package"] = {"pdf_bytes": b"fake_pdf"}
        st.session_state["user_notes"] = "Confidential experiment notes"
        st.session_state["nav_page"] = "results"
        st.session_state["sidebar_page"] = "Results"

        # Now click Quick Demo Access
        handle_quick_demo_access()

        # Check that all stale session state was wiped
        self.assertNotIn("registration_result", st.session_state)
        self.assertNotIn("source_img_data", st.session_state)
        self.assertNotIn("reference_img_data", st.session_state)
        self.assertNotIn("source_filename", st.session_state)
        self.assertNotIn("reference_filename", st.session_state)
        self.assertNotIn("source_metadata", st.session_state)
        self.assertNotIn("reference_metadata", st.session_state)
        self.assertNotIn("homography", st.session_state)
        self.assertNotIn("validation_results", st.session_state)
        self.assertNotIn("export_package", st.session_state)
        self.assertNotIn("user_notes", st.session_state)

        # Fresh demo session starts at Overview
        self.assertEqual(st.session_state["nav_page"], "overview")
        self.assertEqual(st.session_state["sidebar_page"], "Overview")
        self.assertTrue(is_demo_session())

    def test_08_demo_user_does_not_overwrite_existing_account(self):
        """8. Demo user provisioning never overwrites real user accounts."""
        real_email = "real.scientist@isro.gov.in"
        real_pass = "OriginalSecret!99"
        create_user("Original Scientist", real_email, real_pass)

        # Retrieve password hash of real user
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row_before = conn.execute("SELECT * FROM users WHERE email = ?", (real_email,)).fetchone()
            self.assertIsNotNone(row_before)
            hash_before = row_before["password_hash"]
            uid_before = row_before["id"]

        # Call get_or_create_demo_user multiple times
        demo_uid, demo_name, demo_eml = get_or_create_demo_user()
        demo_uid_2, demo_name_2, demo_eml_2 = get_or_create_demo_user()
        self.assertEqual(demo_uid, demo_uid_2)

        # Verify real user is 100% intact
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row_after = conn.execute("SELECT * FROM users WHERE email = ?", (real_email,)).fetchone()
            self.assertIsNotNone(row_after)
            self.assertEqual(row_after["password_hash"], hash_before)
            self.assertEqual(row_after["id"], uid_before)
            self.assertEqual(row_after["full_name"], "Original Scientist")

        # Verify real user can still authenticate
        auth_real = authenticate_user(real_email, real_pass)
        self.assertIsNotNone(auth_real)

    def test_09_apptest_full_ui_quick_demo_access_and_logout(self):
        """9. Full Streamlit AppTest integration: click Quick Demo Access, verify Overview, and verify no warnings."""
        if not APP_PATH or not os.path.exists(APP_PATH):
            self.skipTest("app.py path not resolved for AppTest")

        at = AppTest.from_file(APP_PATH, default_timeout=35)
        at.run()
        self.assertFalse(at.exception, f"Exception on initial load: {at.exception}")

        # Look for Quick Demo Access button on login page
        demo_btns = [b for b in at.button if b.key == "btn_quick_demo_access"]
        self.assertEqual(len(demo_btns), 1, "Quick Demo Access button must be present on Login page")

        # Click Quick Demo Access button
        at_demo = demo_btns[0].click().run()
        self.assertFalse(at_demo.exception, f"Exception on Quick Demo Access click: {at_demo.exception}")

        # Verify authenticated state
        self.assertIn("auth_authenticated", at_demo.session_state)
        self.assertTrue(at_demo.session_state["auth_authenticated"])
        self.assertEqual(at_demo.session_state["auth_name"], DEMO_USER_NAME)
        self.assertEqual(at_demo.session_state["auth_email"], DEMO_USER_EMAIL.lower())
        self.assertTrue(at_demo.session_state["auth_is_demo"])
        self.assertEqual(at_demo.session_state["nav_page"], "overview")

        # Verify no callback rerun warning
        warnings = [w.value for w in at_demo.warning]
        self.assertNotIn(
            "Calling st.rerun() within a callback is a no-op",
            warnings,
            "Streamlit no-op callback warning must NOT be emitted",
        )

        # Look for Sign out button in sidebar while in demo session
        logout_btns = [b for b in at_demo.sidebar.button if b.key == "sidebar_logout_btn"]
        self.assertEqual(len(logout_btns), 1, "Sign out button must be in sidebar during demo session")

        # Click Sign out
        at_logged_out = logout_btns[0].click().run()
        self.assertFalse(at_logged_out.exception, f"Exception on logout: {at_logged_out.exception}")

        # Verify returned to unauthenticated Login page
        auth_flag = at_logged_out.session_state["auth_authenticated"] if "auth_authenticated" in at_logged_out.session_state else False
        self.assertFalse(auth_flag)
        self.assertNotIn("auth_email", at_logged_out.session_state)

        # Verify no callback rerun warning on logout
        logout_warnings = [w.value for w in at_logged_out.warning]
        self.assertNotIn(
            "Calling st.rerun() within a callback is a no-op",
            logout_warnings,
            "Streamlit no-op callback warning must NOT be emitted on logout",
        )

        # Verify Quick Demo Access button is visible again on Login page
        demo_btns_after = [b for b in at_logged_out.button if b.key == "btn_quick_demo_access"]
        self.assertEqual(len(demo_btns_after), 1, "Quick Demo Access button must be present after logout")


if __name__ == "__main__":
    unittest.main()
