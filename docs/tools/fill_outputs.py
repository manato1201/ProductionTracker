#!/usr/bin/env python3
"""講義の「実行結果」を、実際に実行して埋める(執筆用の道具)。

    python docs/tools/fill_outputs.py docs/lectures/L01-web.md [...]

`<!-- output -->` の直後の ```text ブロックの中身が `?` のとき、直前のコード(`<!-- test -->` / `<!-- test:django -->` / `<!-- test:node -->`)を
実行して、標準出力で置き換える。すでに結果が書いてあるものは触らない(値が変わったかは test_docs.py が見る)。
結果を手で貼ると写し間違えるので、このツールで埋めること。
"""

import contextlib
import io
import os
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test")

import django  # noqa: E402

django.setup()

from django.db import transaction  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

RUN_RE = re.compile(
    r"(?P<head><!-- test(?P<mode>:django|:node)? -->\n```(?P<lang>python|javascript)\n(?P<code>.*?)\n```\n\n<!-- output -->\n```text\n)(?P<out>.*?)(?P<tail>\n```)",
    re.S,
)


def run_node(code: str, cwd: Path, name: str) -> str:
    import subprocess

    done = subprocess.run(  # noqa: S603
        ["node", "--no-warnings", "--experimental-transform-types", "--input-type=module", "-"], input=code, cwd=cwd, capture_output=True, text=True, timeout=60  # noqa: S607
    )
    if done.returncode != 0:
        print(done.stderr, file=sys.stderr)
        sys.exit(f"{name}: node の実行に失敗しました")
    return done.stdout.strip()


def run(code: str, django_mode: bool, name: str) -> str:
    buffer = io.StringIO()

    class Rollback(Exception):
        pass

    def body():
        with contextlib.redirect_stdout(buffer):
            exec(compile(code, name, "exec"), {"__name__": "__doc_example__"})  # noqa: S102

    try:
        if django_mode:
            try:
                with transaction.atomic():
                    body()
                    raise Rollback
            except Rollback:
                pass
        else:
            body()
    except Exception:
        traceback.print_exc()
        sys.exit(f"{name}: 実行に失敗しました")
    return buffer.getvalue().strip()


def main(paths: list[str]) -> None:
    setup_test_environment()
    runner = DiscoverRunner(verbosity=0, interactive=False)
    old = runner.setup_databases()
    try:
        for p in paths:
            path = Path(p)
            text = path.read_text(encoding="utf-8")
            count = 0

            def repl(m):
                nonlocal count
                if m.group("out").strip() != "?":
                    return m.group(0)
                line = text.count("\n", 0, m.start()) + 1
                count += 1
                if m.group("mode") == ":node":
                    result = run_node(m.group("code"), path.resolve().parent, f"{path.name}:{line}")
                else:
                    result = run(m.group("code"), m.group("mode") == ":django", f"{path.name}:{line}")
                return m.group("head") + result + m.group("tail")

            new = RUN_RE.sub(repl, text)
            if new != text:
                path.write_text(new, encoding="utf-8")
            print(f"{path}: {count} 件の結果を埋めました")
    finally:
        runner.teardown_databases(old)


if __name__ == "__main__":
    main(sys.argv[1:])
