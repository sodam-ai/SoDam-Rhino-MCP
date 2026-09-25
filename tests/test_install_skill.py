import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.install_skill import (
    LAUNCHER,
    _codex_status,
    _repair_codex_registration,
    install,
)


class InstallSkillTests(unittest.TestCase):
    def test_claude_install_and_repeat_preserve_other_server(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            existing = {"mcpServers": {"other": {"command": "other-server"}}, "setting": 1}
            (project / ".mcp.json").write_text(json.dumps(existing), encoding="utf-8")
            preview = install("claude", project, dry_run=True)
            self.assertEqual(preview["skill_status"], "would_copy")
            self.assertEqual(preview["mcp_status"], "missing")
            self.assertFalse((project / ".claude").exists())
            installed = install("claude", project)
            self.assertEqual(installed["mcp_status"], "ready")
            self.assertEqual(install("claude", project)["mcp_status"], "ready")
            self.assertEqual(install("claude", project, dry_run=True)["mcp_status"], "ready")
            config = json.loads((project / ".mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(config["mcpServers"]["other"], existing["mcpServers"]["other"])
            self.assertEqual(config["setting"], 1)
            self.assertTrue((project / ".claude" / "skills" / "sodam-rhino-architectural-modeling" / "SKILL.md").is_file())

    def test_different_existing_skill_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            skill = project / ".claude" / "skills" / "sodam-rhino-architectural-modeling"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("user content", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                install("claude", project)
            self.assertEqual((skill / "SKILL.md").read_text(encoding="utf-8"), "user content")

    def test_disabled_codex_registration_is_not_ready(self):
        from subprocess import CompletedProcess

        output = f"sodam-rhino-offline\n  enabled: false\n  transport: stdio\n  command: cmd\n  args: /c {LAUNCHER}\n"
        with (patch("scripts.install_skill.shutil.which", return_value="codex"),
              patch("scripts.install_skill.subprocess.run", return_value=CompletedProcess([], 0, output, "")),
              self.assertRaisesRegex(RuntimeError, "disabled")):
            _codex_status()

    def test_failed_codex_query_is_not_mistaken_for_missing(self):
        from subprocess import CompletedProcess

        with (patch("scripts.install_skill.shutil.which", return_value="codex"),
              patch("scripts.install_skill.subprocess.run", return_value=CompletedProcess([], 2, "", "unexpected failure")),
              self.assertRaisesRegex(RuntimeError, "query")):
            _codex_status()

    def test_moved_codex_registration_requires_explicit_repair(self):
        from subprocess import CompletedProcess

        with tempfile.TemporaryDirectory() as directory:
            old = Path(directory) / "removed" / "start_mcp.cmd"
            output = (
                "sodam-rhino-offline\n  enabled: true\n  transport: stdio\n"
                f"  command: cmd\n  args: /c {old}\n  cwd: -\n  env: -\n"
            )
            with (patch("scripts.install_skill.shutil.which", return_value="codex"),
                  patch("scripts.install_skill.subprocess.run",
                        return_value=CompletedProcess([], 0, output, "")) as run):
                with self.assertRaisesRegex(RuntimeError, "points elsewhere"):
                    _codex_status()
                self.assertEqual(_codex_status(allow_stale=True), "stale")
                self.assertEqual(run.call_count, 2)

    def test_moved_codex_registration_rejects_extra_environment(self):
        from subprocess import CompletedProcess

        output = (
            "sodam-rhino-offline\n  enabled: true\n  transport: stdio\n"
            "  command: cmd\n  args: /c Z:\\missing\\start_mcp.cmd\n"
            "  cwd: -\n  env: TEST_FLAG=1\n"
        )
        with (patch("scripts.install_skill.shutil.which", return_value="codex"),
              patch("scripts.install_skill.subprocess.run",
                    return_value=CompletedProcess([], 0, output, "")),
              self.assertRaisesRegex(RuntimeError, "points elsewhere")):
            _codex_status(allow_stale=True)

    def test_repair_moved_codex_registration_changes_only_named_server(self):
        old = str(Path("Z:/missing/start_mcp.cmd"))
        details = {"enabled": "true", "transport": "stdio", "command": "cmd",
                   "args": f"/c {old}", "cwd": "-", "env": "-"}
        with (patch("scripts.install_skill._codex_registration", return_value=("present", details)),
              patch("scripts.install_skill.subprocess.run") as run):
            _repair_codex_registration()
        self.assertEqual(run.call_args_list[0].args[0],
                         ["codex", "mcp", "remove", "sodam-rhino-offline"])
        self.assertEqual(run.call_args_list[1].args[0],
                         ["codex", "mcp", "add", "sodam-rhino-offline", "--",
                          "cmd", "/c", str(LAUNCHER)])
        self.assertEqual(run.call_count, 2)

    def test_failed_repair_restores_previous_registration(self):
        from subprocess import CalledProcessError

        old = str(Path("Z:/missing/start_mcp.cmd"))
        details = {"enabled": "true", "transport": "stdio", "command": "cmd",
                   "args": f"/c {old}", "cwd": "-", "env": "-"}
        with (patch("scripts.install_skill._codex_registration", return_value=("present", details)),
              patch("scripts.install_skill.subprocess.run",
                    side_effect=[None, CalledProcessError(1, "codex"), None]) as run,
              self.assertRaises(CalledProcessError)):
            _repair_codex_registration()
        self.assertEqual(run.call_args_list[2].args[0],
                         ["codex", "mcp", "add", "sodam-rhino-offline", "--",
                          "cmd", "/c", old])

    def test_repair_preview_does_not_change_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            with (patch("scripts.install_skill._codex_status", return_value="stale"),
                  patch("scripts.install_skill._ensure_runtime"),
                  patch("scripts.install_skill.subprocess.run") as run):
                result = install("codex", Path(directory), dry_run=True,
                                 repair_moved_registration=True)
            self.assertEqual(result["mcp_status"], "would_repair")
            run.assert_not_called()

    def test_conflicting_mcp_registration_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config = {"mcpServers": {"sodam-rhino-offline": {"command": "different"}}}
            (project / ".mcp.json").write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                install("claude", project)
            self.assertFalse((project / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
