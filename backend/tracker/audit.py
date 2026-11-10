"""監査ログの記録(版・ノートの変更。設計 S-C)。

呼び出し側は、変更と同じトランザクションの中で `record` を呼ぶ(変更だけ残って記録が無い、を作らない)。
`detail` には、状態や番号などの**短い事実だけ**を入れる。ノートの本文・版のコメント・ファイルの場所は入れない。
"""

from .models import AuditEvent

# detail に入れてよい鍵。これ以外は捨てる(うっかり本文などを渡しても残らない)
ALLOWED_DETAIL_KEYS = frozenset({"number", "status", "from", "to", "task", "body_length", "on_type", "on_id"})


def _actor_name(user) -> str:
    if user is None:
        return "unknown"
    name = user.get_username() if hasattr(user, "get_username") else str(user)
    return (name or "unknown")[:150]


def record(*, user, action: str, project, target_type: str, target_id: int, **detail) -> AuditEvent:
    actor = user if getattr(user, "pk", None) is not None else None
    return AuditEvent.objects.create(
        project=project,
        project_code=project.code,
        actor=actor,
        actor_name=_actor_name(user),
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail={k: v for k, v in detail.items() if k in ALLOWED_DETAIL_KEYS},
    )
