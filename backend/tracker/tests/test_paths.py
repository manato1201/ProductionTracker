import pytest

from tracker.paths import match_entity, normalize_path


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("assets\\props\\crate\\", "assets/props/crate"),
        ("  ./assets//props/crate/  ", "assets/props/crate"),
        ("P:\\proj\\a.fbx", "P:/proj/a.fbx"),
        ("", ""),
    ],
)
def test_normalize_path(raw, expected):
    assert normalize_path(raw) == expected


CANDIDATES = [(1, "assets/props"), (2, "assets/props/crate"), (3, "")]


@pytest.mark.parametrize(
    "path,expected",
    [
        ("assets/props/crate/crate.fbx", 2),  # 最長一致
        ("assets/props/barrel.fbx", 1),
        ("assets/props/crate", 2),  # 完全一致
        ("assets/props/crater/x.fbx", 1),  # 区切りを跨がない前方一致は別物(crate ≠ crater)
        ("ASSETS\\Props\\Crate\\x.fbx", 2),  # 区切り・大文字小文字のずれを吸収
        ("assets/chars/x.fbx", None),
        ("other/assets/props/x.fbx", None),
    ],
)
def test_match_entity(path, expected):
    assert match_entity(path, CANDIDATES) == expected
