#!/usr/bin/env python3
"""Interactive CLI tests for appup, run through a real pty.

Verifies the prompts actually appear at a terminal and answers them like a
user would. Read-only: every upgrade prompt is answered "n".
Run: python3 test_cli.py
"""
import os
import pty
import re
import select
import sys
import time

APPUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appup")


def spawn(args, answers, timeout=180):
    """Run appup <args> in a pty, replying per (pattern, reply); return output."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execv(sys.executable, [sys.executable, APPUP] + args)
    out, buf, pending = "", "", list(answers)
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], 1)
        if not r:
            continue
        try:
            chunk = os.read(fd, 4096).decode(errors="replace")
        except OSError:
            break
        if not chunk:
            break
        out += chunk
        buf += chunk
        if pending and re.search(pending[0][0], buf):
            os.write(fd, pending[0][1].encode())
            buf, pending = "", pending[1:]
    os.close(fd)
    os.waitpid(pid, 0)
    assert not pending, f"prompt never appeared: {pending[0][0]!r}\n--- output:\n{out}"
    return out


def main():
    out = spawn(["outdated", "manual"], [(r"cask catalog.*\[y/N\]", "y\n")])
    assert re.search(r"\d+ manual \.app\(s\) have a newer version", out), out[-500:]
    assert "== manual .app ==" in out
    print("ok: outdated manual prompts and checks the catalog")

    out = spawn(["upgrade", "brew"], [(r"Proceed\? \[y/N\]", "n\n")])
    assert "brew upgrade" in out and "Aborted." in out
    print("ok: upgrade shows commands and aborts on n")

    out = spawn(["upgrade", "manual"],
                [(r"space-separated\): ", "\n"), (r"Proceed\? \[y/N\]", "n\n")])
    assert "brew install --cask --force" in out and "Aborted." in out
    print("ok: upgrade manual offers token selection and aborts on n")

    out = spawn(["upgrade", "manual"], [(r"space-separated\): ", "not-a-token\n")])
    assert "not in the matched list" in out
    print("ok: upgrade manual rejects unknown tokens")


if __name__ == "__main__":
    main()
