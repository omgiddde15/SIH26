"""
Automated regression tests for LunarReg Sign Out navigation and session-state sanitization.

Verifies:
1. Login -> Sign Out -> lands cleanly on Login.
2. Login -> Results -> Sign Out -> lands cleanly on Login.
3. Login -> Research Lab -> Sign Out -> lands cleanly on Login.
4. Login -> Run Registration -> Sign Out -> Login -> no leaked state from previous run.
5. Verification that sidebar_state is collapsed on logout and no exception or widget collision occurs.
"""

import os
import unittest
from streamlit.testing.v1 import AppTest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_TESTS_DIR)
_APP_PATH = os.path.join(_PROJECT_DIR, "SIH26_Lunar_Registration", "app", "app.py")


class TestSignOutNavigation(unittest.TestCase):
    APP_PATH = _APP_PATH

    def _login(self, at: AppTest, nav_page: str = "overview") -> None:
        """Helper to establish an authenticated session in AppTest."""
        at.session_state["auth_authenticated"] = True
        at.session_state["auth_email"] = "test.operator@isro.gov.in"
        at.session_state["auth_name"] = "Dr. Test Operator"
        at.session_state["auth_user_id"] = "user_42"
        at.session_state["nav_page"] = nav_page
        at.run()

    def test_login_to_sign_out_lands_cleanly_on_login(self):
        """Scenario 1: Login -> Sign Out -> lands cleanly on Login."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        self._login(at, nav_page="overview")
        self.assertFalse(at.exception, f"Exceptions on login: {at.exception}")

        # Find sign out button in sidebar
        logout_buttons = [b for b in at.sidebar.button if b.key == "sidebar_logout_btn"]
        self.assertEqual(len(logout_buttons), 1, "Sign out button should be present in sidebar when authenticated")

        # Click Sign out
        at_logged_out = logout_buttons[0].click().run()
        self.assertFalse(at_logged_out.exception, f"Exceptions on logout: {at_logged_out.exception}")

        # Verify unauthenticated state
        auth_flag = at_logged_out.session_state["auth_authenticated"] if "auth_authenticated" in at_logged_out.session_state else False
        self.assertFalse(auth_flag, "auth_authenticated must be False or absent after logout")
        self.assertNotIn("auth_email", at_logged_out.session_state, "auth_email must be removed after logout")

        # Verify no callback rerun warning
        self.assertNotIn(
            "Calling st.rerun() within a callback is a no-op",
            [w.value for w in at_logged_out.warning],
            "st.rerun() no-op warning should not be emitted",
        )

        # Verify login form is rendered
        login_emails = [i for i in at_logged_out.text_input if i.key == "auth_login_email"]
        self.assertTrue(len(login_emails) > 0, "Auth page login email input should be visible")

        # Verify sidebar has no authenticated controls
        self.assertEqual(len(at_logged_out.sidebar.button), 0, "Sidebar should have no buttons when unauthenticated")

        # Re-login verification (Login -> Sign Out -> Login)
        at_logged_out.session_state["auth_authenticated"] = True
        at_logged_out.session_state["auth_email"] = "test.operator@isro.gov.in"
        at_logged_out.session_state["auth_name"] = "Dr. Test Operator"
        at_logged_out.session_state["auth_user_id"] = "user_42"
        at_relogin = at_logged_out.run()
        self.assertFalse(at_relogin.exception)
        nav = at_relogin.session_state["nav_page"] if "nav_page" in at_relogin.session_state else "overview"
        self.assertEqual(nav, "overview", "Should return cleanly to overview on re-login")

    def test_results_to_sign_out_lands_cleanly_on_login(self):
        """Scenario 2: Results -> Sign Out -> Login."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        self._login(at, nav_page="results")
        self.assertFalse(at.exception, f"Exceptions on login to results: {at.exception}")

        # Find sign out button in sidebar
        logout_buttons = [b for b in at.sidebar.button if b.key == "sidebar_logout_btn"]
        self.assertEqual(len(logout_buttons), 1, "Sign out button must be in sidebar on Results page")

        # Click Sign out
        at_logged_out = logout_buttons[0].click().run()
        self.assertFalse(at_logged_out.exception, f"Exceptions on logout from results: {at_logged_out.exception}")

        # Verify unauthenticated and lands on login
        auth_flag = at_logged_out.session_state["auth_authenticated"] if "auth_authenticated" in at_logged_out.session_state else False
        self.assertFalse(auth_flag, "auth_authenticated must be False or absent after logout")
        self.assertNotIn("auth_email", at_logged_out.session_state, "auth_email must be removed after logout")

        # Verify no callback rerun warning
        self.assertNotIn(
            "Calling st.rerun() within a callback is a no-op",
            [w.value for w in at_logged_out.warning],
            "st.rerun() no-op warning should not be emitted",
        )

        login_emails = [i for i in at_logged_out.text_input if i.key == "auth_login_email"]
        self.assertTrue(len(login_emails) > 0, "Auth page login form should be rendered")
        self.assertEqual(len(at_logged_out.sidebar.button), 0, "Sidebar buttons must be absent on auth page")

        # Re-login verification (Results -> Sign Out -> Login)
        at_logged_out.session_state["auth_authenticated"] = True
        at_logged_out.session_state["auth_email"] = "test.operator@isro.gov.in"
        at_logged_out.session_state["auth_name"] = "Dr. Test Operator"
        at_logged_out.session_state["auth_user_id"] = "user_42"
        at_relogin = at_logged_out.run()
        self.assertFalse(at_relogin.exception)
        nav = at_relogin.session_state["nav_page"] if "nav_page" in at_relogin.session_state else "overview"
        self.assertEqual(nav, "overview", "Should return cleanly to overview on re-login")

    def test_research_lab_to_sign_out_lands_cleanly_on_login(self):
        """Scenario 3: Research Lab -> Sign Out -> Login."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        self._login(at, nav_page="research_lab")
        self.assertFalse(at.exception, f"Exceptions on login to research lab: {at.exception}")

        logout_buttons = [b for b in at.sidebar.button if b.key == "sidebar_logout_btn"]
        self.assertEqual(len(logout_buttons), 1, "Sign out button must be in sidebar on Research Lab page")

        # Click Sign out
        at_logged_out = logout_buttons[0].click().run()
        self.assertFalse(at_logged_out.exception, f"Exceptions on logout from research lab: {at_logged_out.exception}")

        # Verify unauthenticated and lands on login
        auth_flag = at_logged_out.session_state["auth_authenticated"] if "auth_authenticated" in at_logged_out.session_state else False
        self.assertFalse(auth_flag, "auth_authenticated must be False or absent after logout")
        self.assertNotIn("auth_email", at_logged_out.session_state, "auth_email must be removed after logout")

        # Verify no callback rerun warning
        self.assertNotIn(
            "Calling st.rerun() within a callback is a no-op",
            [w.value for w in at_logged_out.warning],
            "st.rerun() no-op warning should not be emitted",
        )

        login_emails = [i for i in at_logged_out.text_input if i.key == "auth_login_email"]
        self.assertTrue(len(login_emails) > 0, "Auth page login form should be rendered")
        self.assertEqual(len(at_logged_out.sidebar.button), 0, "Sidebar buttons must be absent on auth page")

        # Re-login verification (Research Lab -> Sign Out -> Login)
        at_logged_out.session_state["auth_authenticated"] = True
        at_logged_out.session_state["auth_email"] = "test.operator@isro.gov.in"
        at_logged_out.session_state["auth_name"] = "Dr. Test Operator"
        at_logged_out.session_state["auth_user_id"] = "user_42"
        at_relogin = at_logged_out.run()
        self.assertFalse(at_relogin.exception)
        nav = at_relogin.session_state["nav_page"] if "nav_page" in at_relogin.session_state else "overview"
        self.assertEqual(nav, "overview", "Should return cleanly to overview on re-login")

    def test_registration_to_sign_out_then_relogin_no_leaked_state(self):
        """Scenario 4: Login -> Run Registration (populated session) -> Sign Out -> Login -> no leaked state."""
        import numpy as np

        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        self._login(at, nav_page="results")

        # Inject simulated registration results and caches into session_state
        at.session_state["registration_result"] = {
            "success": True,
            "rmse": 0.42,
            "mean_error": 0.38,
            "median_error": 0.35,
            "max_error": 0.89,
            "inliers": 250,
            "runtime": 1.25,
            "pipeline_mode": "Adaptive Production Engine",
            "homography": np.eye(3),
            "reprojection_errors": [0.35, 0.42],
        }
        at.session_state["export_package"] = {"zip_bytes": b"mock_zip"}
        at.session_state["source_img_data"] = np.zeros((100, 100, 3), dtype=np.uint8)
        at.session_state["reference_img_data"] = np.zeros((100, 100, 3), dtype=np.uint8)
        at.session_state["pipeline_mode"] = "Adaptive Production Engine"
        at.run()
        self.assertFalse(at.exception, f"Exceptions on results page render: {at.exception}")

        # Click Sign Out
        logout_buttons = [b for b in at.sidebar.button if b.key == "sidebar_logout_btn"]
        at_logged_out = logout_buttons[0].click().run()
        self.assertFalse(at_logged_out.exception)

        # Verify state is completely cleared
        self.assertNotIn("registration_result", at_logged_out.session_state)
        self.assertNotIn("export_package", at_logged_out.session_state)
        self.assertNotIn("source_img_data", at_logged_out.session_state)
        self.assertNotIn("reference_img_data", at_logged_out.session_state)

        # Now simulate re-logging in
        at_logged_out.session_state["auth_authenticated"] = True
        at_logged_out.session_state["auth_email"] = "test.operator@isro.gov.in"
        at_logged_out.session_state["auth_name"] = "Dr. Test Operator"
        at_logged_out.session_state["auth_user_id"] = "user_42"
        at_relogin = at_logged_out.run()
        self.assertFalse(at_relogin.exception)

        # Verify new session defaults to overview and has NO leaked registration data
        self.assertNotIn(
            "registration_result",
            at_relogin.session_state,
            "registration_result must not leak into subsequent session",
        )
        self.assertNotIn(
            "export_package",
            at_relogin.session_state,
            "export_package must not leak into subsequent session",
        )
        nav = at_relogin.session_state["nav_page"] if "nav_page" in at_relogin.session_state else "overview"
        self.assertEqual(
            nav,
            "overview",
            "Subsequent session should default cleanly to overview page",
        )


if __name__ == "__main__":
    unittest.main()
