"""ドキュメントを壊れにくくするテスト。

講義・ガイドに載せたコードが、本当に動いて、実際のソースと一致していることを確かめる。
- `<!-- test -->` の直後の ```python は実行する(`<!-- test:django -->` は DB が使える状態で実行)。
    `<!-- test:node -->` の直後の ```javascript は Node で実行する(文書のあるフォルダが作業ディレクトリ。
    `../../frontend/src/...ts` のように、実際の TypeScript のソースを import できる)。
    直後に `<!-- output -->` と ```text があれば、標準出力がそれと一致すること。
- `<!-- excerpt: パス -->` の直後のコードブロックは、そのファイルからの抜粋。各行(空行と `...` を除く)が
    実際のファイルにあること(ソースを直したのに文書が古い、を防ぐ)。
- HTML 版が古くなっていないこと・リンク切れが無いこと(`docs/tools/build_html.py --check`)。
- mermaid の図の種類が、描画できるものであること(実際の描画は build_html.py)。
- 文中のコード表記のファイルパスが、実在すること。
"""

import contextlib
import importlib.util
import io
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = ROOT / "docs"


def doc_files():
    files = [ROOT / "README.md"]
    for p in sorted(DOCS_DIR.rglob("*.md")):
        parts = p.relative_to(DOCS_DIR).parts
        if parts[0] in ("html", "tools") or "node_modules" in parts:
            continue
        files.append(p)
    return files


RUN_RE = re.compile(
    r"<!-- test(?P<mode>:django|:node)? -->\n```(?P<lang>python|javascript)\n(?P<code>.*?)\n```"
    r"(?:\n\n<!-- output -->\n```text\n(?P<out>.*?)\n```)?",
    re.S,
)
EXCERPT_RE = re.compile(r"<!-- excerpt: (?P<path>\S+) -->\n```(?P<lang>\w*)\n(?P<code>.*?)\n```", re.S)
MERMAID_RE = re.compile(r"^```mermaid[ \t]*\n(.*?)\n```[ \t]*$", re.M | re.S)
MERMAID_KINDS = ("flowchart", "graph", "sequenceDiagram", "stateDiagram-v2", "erDiagram", "classDiagram", "gantt", "pie", "journey", "mindmap", "timeline")

ELLIPSIS = {"...", "…", "# ...", "// ...", "/* ... */", "# …", "// …", "{/* ... */}"}


def cases(regex):
    out = []
    for path in doc_files():
        text = path.read_text(encoding="utf-8")
        for m in regex.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            # Django の ORM を使う例(`<!-- test:django -->`)は、DB が使える状態で実行する
            marks = [pytest.mark.django_db] if "mode" in regex.groupindex and m.group("mode") == ":django" else []
            out.append(pytest.param(path, line, m, id=f"{path.relative_to(ROOT)}:{line}", marks=marks))
    return out


# ---------------------------------------------------------------------------
# 実行して確かめる
# ---------------------------------------------------------------------------
RUN_CASES = cases(RUN_RE)


@pytest.mark.parametrize(("path", "line", "match"), RUN_CASES)
def test_documented_code_runs(path, line, match):
    code = match.group("code")
    if match.group("mode") == ":node":
        if shutil.which("node") is None:
            pytest.skip("node が無い")
        if "react_demo" in code and not (ROOT / "frontend" / "node_modules" / "react").exists():
            pytest.skip("frontend/node_modules が無い(cd frontend && npm ci)")
        done = subprocess.run(  # noqa: S603
            ["node", "--no-warnings", "--experimental-transform-types", "--input-type=module", "-"],  # noqa: S607
            input=code, cwd=path.parent, capture_output=True, text=True, timeout=60,
        )
        assert done.returncode == 0, f"{path.name}:{line} が失敗:\n{done.stderr[-800:]}"
        output = done.stdout
    else:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile(code, f"{path.name}:{line}", "exec"), {"__name__": "__doc_example__"})  # noqa: S102
        output = buffer.getvalue()
    expected = match.group("out")
    if expected is not None:
        assert output.strip() == expected.strip(), f"{path.name}:{line} の出力が文書の『実行結果』と違う"


def test_there_are_runnable_examples_in_lectures():
    """講義に、実行して確かめるコードが十分にあること(0 件だと、この仕組み自体が壊れていても気づけない)。"""
    lecture_cases = [c for c in RUN_CASES if "docs/lectures" in str(c.values[0])]
    assert len(lecture_cases) >= 25


# ---------------------------------------------------------------------------
# 抜粋が実際のソースと一致している
# ---------------------------------------------------------------------------
EXCERPT_CASES = cases(EXCERPT_RE)


@pytest.mark.parametrize(("path", "line", "match"), EXCERPT_CASES)
def test_excerpts_match_the_source(path, line, match):
    source_path = ROOT / match.group("path")
    assert source_path.exists(), f"{path.name}:{line} 抜粋の元のファイルが無い: {match.group('path')}"
    source_lines = {ln.strip() for ln in source_path.read_text(encoding="utf-8").splitlines()}
    missing = []
    for ln in match.group("code").splitlines():
        s = ln.strip()
        if not s or s in ELLIPSIS:
            continue
        if s not in source_lines:
            missing.append(s)
    assert not missing, f"{path.name}:{line} の抜粋が {match.group('path')} に無い行: {missing[:3]}"


def test_there_are_excerpts_in_lectures():
    assert len([c for c in EXCERPT_CASES if "docs/lectures" in str(c.values[0])]) >= 30


# ---------------------------------------------------------------------------
# mermaid / リンク / HTML 版 / パス表記
# ---------------------------------------------------------------------------
MERMAID_CASES = cases(MERMAID_RE)


@pytest.mark.parametrize(("path", "line", "match"), MERMAID_CASES)
def test_mermaid_blocks_have_a_known_diagram_type(path, line, match):
    first = next(ln.strip() for ln in match.group(1).splitlines() if ln.strip() and not ln.strip().startswith("%%"))
    assert first.startswith(MERMAID_KINDS), f"{path.name}:{line} 図の種類が分からない: {first[:30]}"
    assert match.group(1).count("```") == 0


def load_builder():
    pytest.importorskip("markdown_it")
    pytest.importorskip("mdit_py_plugins")
    pytest.importorskip("pygments")
    spec = importlib.util.spec_from_file_location("build_html", DOCS_DIR / "tools" / "build_html.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_html_is_up_to_date_and_links_are_valid(capsys):
    """HTML 版が Markdown と同期していて、リンク・見出しへのリンクが切れていない。
    古いときは `python docs/tools/build_html.py` で作り直す。"""
    builder = load_builder()
    code = builder.main(["--check"])
    err = capsys.readouterr().err
    assert code == 0, f"\n{err}"


CODE_PATH_RE = re.compile(r"`((?:backend|frontend|docs|scripts)/[A-Za-z0-9_./\-]+)`")


def test_file_paths_written_in_docs_exist():
    """文中に `backend/tracker/models.py` のように書いたパスが、実在する(リネームの追従漏れを防ぐ)。"""
    missing = []
    for path in doc_files():
        text = path.read_text(encoding="utf-8")
        text = MERMAID_RE.sub("", text)
        for m in CODE_PATH_RE.finditer(text):
            p = m.group(1).rstrip("/.")
            if "*" in p or "<" in p:
                continue
            if not (ROOT / p).exists():
                missing.append(f"{path.relative_to(ROOT)}: {p}")
    assert not missing, "実在しないパス:\n" + "\n".join(missing[:20])


def test_docs_contain_no_control_characters():
    """文書に NUL などの制御文字が混ざっていない(実行結果の貼り付けで混ざりやすい)。"""
    bad = []
    for path in doc_files():
        text = path.read_text(encoding="utf-8")
        for i, ch in enumerate(text):
            if ord(ch) < 32 and ch not in "\n\t\r":
                bad.append(f"{path.relative_to(ROOT)}: U+{ord(ch):04X} (位置 {i})")
                break
    assert not bad, "\n".join(bad)
