"""アセットパスの正規化と突き合わせ(AssetDataInsightSuite の結果 ↔ Entity.path)。

対応は「パスの前方一致」から始める(設計書 4)。区切りは / に揃え、大文字小文字は区別しない
(Windows のドライブ文字 `P:` / `p:` のずれを吸収するため)。
実データで表記がずれる場合は、ここに対応表を足す。
"""

import re

_MULTI_SLASH = re.compile(r"/{2,}")


def normalize_path(path: str) -> str:
    p = path.strip().replace("\\", "/")
    p = _MULTI_SLASH.sub("/", p)
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/")


def _key(path: str) -> str:
    return normalize_path(path).casefold()


def match_entity(asset_path: str, candidates: list[tuple[int, str]]) -> int | None:
    """`candidates` = [(entity_id, entity_path)]。最も長く前方一致した Entity の id を返す。"""
    target = _key(asset_path)
    best_id, best_len = None, -1
    for entity_id, entity_path in candidates:
        prefix = _key(entity_path)
        if not prefix:
            continue
        if (target == prefix or target.startswith(prefix + "/")) and len(prefix) > best_len:
            best_id, best_len = entity_id, len(prefix)
    return best_id
