"""Install the offline skill and MCP without replacing unrelated configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "sodam-rhino-architectural-modeling"
SERVER_NAME = "sodam-rhino-offline"
LAUNCHER = ROOT / "start_mcp.cmd"


def _digest_tree(path: Path) -> dict[str, str]:
    return {
        str(file.relative_to(path)).replace("\\", "/"): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in path.rglob("*")
        if file.is_file()
    }


def _runtime_python() -> Path:
    return ROOT / ".venv" / "Scripts" / "python.exe"


def _requirements() -> dict[str, str]:
    return dict(line.strip().split("==", 1) for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() if line.strip())


def _check_runtime() -> None:
    python = _runtime_python()
    if not python.is_file():
        raise RuntimeError("isolated Python runtime is missing")
    checker = "import importlib.metadata as m, json, sys; print(json.dumps({'python':list(sys.version_info[:2]), 'packages':{n:m.version(n) for n in sys.argv[1:]}}))"
    result = subprocess.run([str(python), "-c", checker, *_requirements()], capture_output=True, text=True, check=True)
    installed = json.loads(result.stdout)
    if installed["python"] != [3, 12] or installed["packages"] != _requirements():
        raise RuntimeError(f"runtime differs from pinned requirements: {installed}")


def _ensure_runtime(dry_run: bool) -> None:
    if _runtime_python().exists():
        _check_runtime()
        return
    if dry_run:
        return
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("run installer with Python 3.12, for example: py -3.12 scripts/install_skill.py")
    subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    subprocess.run([str(_runtime_python()), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
    _check_runtime()


def _codex_registration() -> tuple[str, dict[str, str]]:
    if shutil.which("codex") is None:
        raise RuntimeError("Codex CLI is unavailable; skill and MCP cannot both be installed")
    result = subprocess.run(["codex", "mcp", "get", SERVER_NAME], capture_output=True, text=True, check=False)
    if result.returncode:
        if f"No MCP server named '{SERVER_NAME}' found." in result.stderr:
            return "missing", {}
        raise RuntimeError("Codex MCP registration query failed")
    details = dict(line.strip().split(": ", 1) for line in result.stdout.splitlines() if ": " in line)
    return "present", details


def _codex_registration_status(state: str, details: dict[str, str],
                               allow_stale: bool = False) -> str:
    if state == "missing":
        return "missing"
    if details.get("enabled") != "true":
        raise RuntimeError(f"{SERVER_NAME} is disabled or its enabled status is unknown")
    expected = {"transport": "stdio", "command": "cmd", "args": f"/c {LAUNCHER}"}
    if any(details.get(key) != value for key, value in expected.items()):
        old_arg = details.get("args", "")
        old_path = Path(old_arg[3:]) if old_arg.startswith("/c ") else None
        if (allow_stale and details.get("transport") == "stdio" and
                details.get("command") == "cmd" and old_path is not None and
                old_path.is_absolute() and
                old_path.name.lower() == LAUNCHER.name.lower() and
                not old_path.is_file() and details.get("cwd") == "-" and
                details.get("env") == "-"):
            return "stale"
        raise RuntimeError(f"{SERVER_NAME} already points elsewhere; inspect it before changing its registration")
    return "ready"


def _codex_status(allow_stale: bool = False) -> str:
    state, details = _codex_registration()
    return _codex_registration_status(state, details, allow_stale)


def _repair_codex_registration() -> None:
    state, details = _codex_registration()
    if _codex_registration_status(state, details, allow_stale=True) != "stale":
        raise RuntimeError("Codex registration changed; inspect it before retrying")
    old_path = details["args"][3:]
    subprocess.run(["codex", "mcp", "remove", SERVER_NAME], check=True)
    try:
        subprocess.run(["codex", "mcp", "add", SERVER_NAME, "--", "cmd", "/c", str(LAUNCHER)], check=True)
    except (OSError, subprocess.CalledProcessError):
        subprocess.run(["codex", "mcp", "add", SERVER_NAME, "--", "cmd", "/c", old_path], check=True)
        raise


def _claude_config(project: Path) -> tuple[Path, dict, bool]:
    path = project / ".mcp.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
        raise TypeError("existing .mcp.json does not have an object mcpServers field")
    servers = data.setdefault("mcpServers", {})
    expected = {"command": "cmd", "args": ["/c", str(LAUNCHER)]}
    existing = servers.get(SERVER_NAME)
    if existing is not None and existing != expected:
        raise RuntimeError(f"{SERVER_NAME} already points elsewhere in .mcp.json")
    if existing is None:
        servers[SERVER_NAME] = expected
        return path, data, True
    return path, data, False


def _write_claude_config(path: Path, data: dict) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".mcp.", suffix=".tmp", delete=False) as stream:
        stage = Path(stream.name)
        stream.write(content)
    try:
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)


def install(host: str, project: Path, dry_run: bool = False,
            repair_moved_registration: bool = False) -> dict:
    project = project.resolve(strict=True)
    if not project.is_dir():
        raise ValueError("project must be an existing directory")
    if not SKILL.joinpath("SKILL.md").is_file() or not LAUNCHER.is_file():
        raise RuntimeError("source skill or launcher is missing")
    destination = project / (".agents" if host == "codex" else ".claude") / "skills" / SKILL.name
    expected_files = _digest_tree(SKILL)
    if destination.exists() and _digest_tree(destination) != expected_files:
        raise FileExistsError(f"different skill already exists: {destination}")
    server_status = (_codex_status(allow_stale=repair_moved_registration)
                     if host == "codex" else ("missing" if _claude_config(project)[2] else "ready"))
    _ensure_runtime(dry_run)
    if dry_run:
        return {"host": host, "skill": str(destination), "skill_status": "exists" if destination.exists() else "would_copy", "mcp_status": "would_repair" if server_status == "stale" else server_status, "dry_run": True}
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".sodam-skill-", dir=destination.parent))
        try:
            shutil.copytree(SKILL, stage, dirs_exist_ok=True)
            if _digest_tree(stage) != expected_files:
                raise RuntimeError("skill copy verification failed")
            stage.rename(destination)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    if host == "codex" and server_status == "missing":
        subprocess.run(["codex", "mcp", "add", SERVER_NAME, "--", "cmd", "/c", str(LAUNCHER)], check=True)
    elif host == "codex" and server_status == "stale":
        _repair_codex_registration()
    elif host == "claude":
        config_path, config, missing = _claude_config(project)
        if missing:
            _write_claude_config(config_path, config)
    if _digest_tree(destination) != expected_files:
        raise RuntimeError("installed skill differs from source")
    if host == "codex" and _codex_status() != "ready":
        raise RuntimeError("Codex MCP registration was not verified")
    if host == "claude" and _claude_config(project)[2]:
        raise RuntimeError("Claude MCP registration was not verified")
    return {"host": host, "skill": str(destination), "skill_status": "installed", "mcp_status": "ready", "dry_run": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["codex", "claude"], required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repair-moved-registration", action="store_true",
                        help="replace only this server's unavailable old start_mcp.cmd registration")
    args = parser.parse_args()
    print(json.dumps(install(args.host, args.project, args.dry_run,
                             args.repair_moved_registration), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
