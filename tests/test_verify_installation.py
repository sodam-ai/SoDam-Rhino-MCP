import subprocess
import unittest
from unittest.mock import patch

from scripts.verify_installation import check_claude_host, run_check


class VerifyInstallationTests(unittest.TestCase):
    def test_failing_check_is_reported_without_spilling_child_output(self):
        failed = subprocess.CompletedProcess(["test"], 3, "private stdout", "private stderr")
        with (patch("scripts.verify_installation.subprocess.run", return_value=failed),
              self.assertRaisesRegex(RuntimeError, "exit 3") as error):
            run_check("render", ["test"])
        self.assertNotIn("private", str(error.exception))

    def test_timeout_is_failure(self):
        with (patch("scripts.verify_installation.subprocess.run", side_effect=subprocess.TimeoutExpired(["test"], 1)),
              self.assertRaisesRegex(RuntimeError, "TimeoutExpired")):
            run_check("render", ["test"])

    def test_claude_logged_out_fails_before_mcp_check(self):
        auth = subprocess.CompletedProcess(["claude"], 1, '{"loggedIn": false}', "")
        with (patch("scripts.verify_installation.run_check", return_value=auth) as check,
              self.assertRaisesRegex(RuntimeError, "not signed in")):
            check_claude_host()
        self.assertEqual(check.call_count, 1)

    def test_unreadable_claude_auth_fails_without_raw_output(self):
        auth = subprocess.CompletedProcess(["claude"], 1, "private invalid response", "")
        with (patch("scripts.verify_installation.run_check", return_value=auth),
              self.assertRaisesRegex(RuntimeError, "unreadable") as error):
            check_claude_host()
        self.assertNotIn("private", str(error.exception))

    def test_claude_pending_approval_fails(self):
        auth = subprocess.CompletedProcess(["claude"], 0, '{"loggedIn": true}', "")
        pending = subprocess.CompletedProcess(["claude"], 0, "Status: Pending approval\n", "")
        with (patch("scripts.verify_installation.run_check", side_effect=[auth, pending]),
              self.assertRaisesRegex(RuntimeError, "not connected")):
            check_claude_host()

    def test_claude_connected_passes(self):
        auth = subprocess.CompletedProcess(["claude"], 0, '{"loggedIn": true}', "")
        connected = subprocess.CompletedProcess(["claude"], 0, "Status: ✔ Connected\n", "")
        with patch("scripts.verify_installation.run_check", side_effect=[auth, connected]):
            check_claude_host()


if __name__ == "__main__":
    unittest.main()
