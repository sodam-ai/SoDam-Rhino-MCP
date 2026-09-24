"""Check registration and the real license-free MCP modeling workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
DEFAULT_BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe")


def run_check(name: str, command: list[str], *, env: dict[str, str] | None = None, timeout: int = 180, announce: bool = True, allowed_exit_codes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{name}: could not complete ({type(exc).__name__})") from exc
    if result.returncode not in allowed_exit_codes:
        raise RuntimeError(f"{name}: failed (exit {result.returncode}); run this check separately for details")
    if announce:
        print(f"PASS {name}")
    return result


def check_claude_host() -> None:
    executable = shutil.which("claude.cmd" if os.name == "nt" else "claude")
    if executable is None:
        raise RuntimeError("Claude Code CLI is unavailable")
    auth = run_check("Claude authentication", [executable, "auth", "status", "--json"], timeout=20, announce=False, allowed_exit_codes=(0, 1))
    try:
        logged_in = json.loads(auth.stdout).get("loggedIn") is True
    except (ValueError, AttributeError) as exc:
        raise RuntimeError("Claude authentication status is unreadable") from exc
    if not logged_in:
        raise RuntimeError("Claude Code is not signed in; configuration alone does not prove host operation")
    if auth.returncode != 0:
        raise RuntimeError("Claude authentication status failed")
    server = run_check("Claude MCP connection", [executable, "mcp", "get", "sodam-rhino-offline"], timeout=20, announce=False)
    statuses = [line.split("Status:", 1)[1].strip() for line in server.stdout.splitlines() if "Status:" in line]
    if len(statuses) != 1 or re.fullmatch(r"\W*Connected\W*", statuses[0]) is None:
        raise RuntimeError("Claude project MCP is not connected; open Claude Code and approve the server")
    print("PASS Claude authentication and MCP connection")


def verify(host: str, blender: Path) -> None:
    if not PYTHON.is_file():
        raise RuntimeError("project .venv Python is missing; run the documented installer")
    preview = run_check("registration and pinned runtime", [str(PYTHON), "scripts/install_skill.py", "--host", host, "--project", str(ROOT), "--dry-run"], announce=False)
    status = json.loads(preview.stdout)
    if status.get("skill_status") != "exists" or status.get("mcp_status") != "ready":
        raise RuntimeError(f"installation is incomplete: skill={status.get('skill_status')}, MCP={status.get('mcp_status')}")
    print("PASS registration and pinned runtime")
    if host == "claude":
        check_claude_host()
    run_check("launcher and tool discovery", [str(PYTHON), "scripts/smoke_launcher.py"])
    run_check("MCP model, reopen, evidence and image workflow", [str(PYTHON), "scripts/smoke_mcp.py"])
    if not blender.is_file():
        raise RuntimeError("Blender executable is missing; set SODAM_BLENDER_EXE to an existing Blender executable")
    environment = dict(os.environ, SODAM_BLENDER_EXE=str(blender))
    run_check("MCP Blender render and 3DM round trip", [str(PYTHON), "scripts/smoke_blender_mcp.py"], env=environment, timeout=300)
    print("PASS all installation and operational checks")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("codex", "claude"), default="codex")
    parser.add_argument("--blender-exe", type=Path, default=Path(os.environ.get("SODAM_BLENDER_EXE", DEFAULT_BLENDER)))
    args = parser.parse_args()
    try:
        verify(args.host, args.blender_exe)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
