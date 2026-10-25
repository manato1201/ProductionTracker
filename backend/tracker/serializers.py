from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Entity,
    Note,
    Project,
    ProjectMember,
    QualityReport,
    Step,
    Task,
    Version,
    VisualResult,
)
from .paths import normalize_path
from .permissions import visible_entities, visible_projects, visible_tasks

User = get_user_model()


def display_name(user) -> str:
    if user is None:
        return ""
    return user.get_full_name() or user.get_username()


# --- 利用者から見えるものだけを選べる関連フィールド ---
class _VisibleField(serializers.PrimaryKeyRelatedField):
    visible = None  # callable(user) -> queryset

    def get_queryset(self):
        return type(self).visible(self.context["request"].user)


class VisibleProjectField(_VisibleField):
    visible = staticmethod(visible_projects)


class VisibleEntityField(_VisibleField):
    visible = staticmethod(visible_entities)


class VisibleTaskField(_VisibleField):
    visible = staticmethod(visible_tasks)


# --- ユーザー ---
class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "is_staff"]

    def get_display_name(self, obj):
        return display_name(obj)


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source="user_id")
    username = serializers.CharField(source="user.username")
    display_name = serializers.SerializerMethodField()
    role_label = serializers.CharField(source="get_role_display")

    class Meta:
        model = ProjectMember
        fields = ["user", "username", "display_name", "role", "role_label"]

    def get_display_name(self, obj):
        return display_name(obj.user)


# --- プロジェクト ---
class ProjectSerializer(serializers.ModelSerializer):
    task_counts = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()
    can_write = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "code", "name", "start", "due",
            "task_counts", "progress", "my_role", "can_write", "can_review",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_code(self, value):
        if self.instance is not None:
            if value != self.instance.code:
                raise serializers.ValidationError("コードは作成後に変更できません。")
            return value
        # DB の制約は大文字小文字を区別しない(demo と DEMO は同じ)。DRF は式の制約を検査しないので、ここで先に弾く。
        if Project.objects.filter(code__iexact=value).exists():
            raise serializers.ValidationError("このコードは既に使われています(大文字小文字の違いも同じ扱いです)。")
        return value

    def validate(self, attrs):
        start = attrs.get("start", getattr(self.instance, "start", None))
        due = attrs.get("due", getattr(self.instance, "due", None))
        if start and due and due < start:
            raise serializers.ValidationError({"due": "期日は開始日以降にしてください。"})
        return attrs

    def get_task_counts(self, obj):
        # 一覧では viewset の annotate(n_<状態>)を使う。無ければ数える(作成直後など)。状態の一覧は Task.Status から導く。
        annotated = hasattr(obj, f"n_{Task.Status.values[0]}")
        counts = {
            status: getattr(obj, f"n_{status}")
            if annotated
            else Task.objects.filter(entity__project=obj, status=status).count()
            for status in Task.Status.values
        }
        counts["total"] = sum(counts.values())
        return counts

    def get_progress(self, obj):
        counts = self.get_task_counts(obj)
        return round(counts["done"] / counts["total"], 4) if counts["total"] else 0.0

    def _role(self, obj):
        if hasattr(obj, "my_role"):
            return obj.my_role
        return obj.role_for(self.context["request"].user)

    def get_my_role(self, obj):
        return self._role(obj)

    def get_can_write(self, obj):
        return Project.can_write_as(self._role(obj), self.context["request"].user.is_staff)

    def get_can_review(self, obj):
        return Project.can_review_as(self._role(obj))


# --- アセット ---
class EntitySerializer(serializers.ModelSerializer):
    project = VisibleProjectField()
    project_code = serializers.CharField(source="project.code", read_only=True)
    task_count = serializers.SerializerMethodField()
    done_count = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = [
            "id", "project", "project_code", "name", "kind", "status", "path",
            "task_count", "done_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_kind(self, value):
        if value != Entity.Kind.ASSET:
            raise serializers.ValidationError("現在は asset のみ対応しています(shot は未実装)。")
        return value

    def validate_path(self, value):
        return normalize_path(value)

    def validate(self, attrs):
        if self.instance is not None and "project" in attrs and attrs["project"] != self.instance.project:
            raise serializers.ValidationError({"project": "プロジェクトは変更できません。"})
        return attrs

    def get_task_count(self, obj):
        return obj.task_count if hasattr(obj, "task_count") else obj.tasks.count()

    def get_done_count(self, obj):
        return obj.done_count if hasattr(obj, "done_count") else obj.tasks.filter(status="done").count()


# --- 工程 ---
class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ["id", "code", "name", "order"]


# --- タスク ---
class TaskSerializer(serializers.ModelSerializer):
    entity = VisibleEntityField()
    entity_name = serializers.CharField(source="entity.name", read_only=True)
    project = serializers.IntegerField(source="entity.project_id", read_only=True)
    project_code = serializers.CharField(source="entity.project.code", read_only=True)
    step = serializers.PrimaryKeyRelatedField(queryset=Step.objects.all())
    step_name = serializers.CharField(source="step.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), allow_null=True, required=False)
    assignee_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    next_statuses = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "entity", "entity_name", "project", "project_code", "step", "step_name",
            "status", "status_label", "priority", "priority_label",
            "assignee", "assignee_name", "due", "estimate_h", "is_overdue", "version_count",
            "next_statuses", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]  # 状態は transition でのみ変える

    def validate_estimate_h(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("見積は 0 以上にしてください。")
        return value

    def validate(self, attrs):
        if self.instance is not None:
            for field in ("entity", "step"):
                if field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError({field: "作成後に変更できません。"})
        entity = attrs.get("entity") or getattr(self.instance, "entity", None)
        assignee = attrs.get("assignee")
        if assignee is not None and entity is not None:
            is_member = ProjectMember.objects.filter(project=entity.project, user=assignee).exists()
            if not (is_member or assignee.is_staff):
                raise serializers.ValidationError({"assignee": "担当者はプロジェクトのメンバーから選んでください。"})
        return attrs

    def get_assignee_name(self, obj):
        return display_name(obj.assignee)

    def get_is_overdue(self, obj):
        return bool(obj.due and obj.status != Task.Status.DONE and obj.due < timezone.localdate())

    def get_version_count(self, obj):
        return obj.version_count if hasattr(obj, "version_count") else obj.versions.count()

    def get_next_statuses(self, obj):
        # 遷移表(Task.TRANSITIONS)の結果。権限や追加条件は見ない(最終判断はサーバーの transition)
        order = list(Task.Status.values)
        return sorted((str(s) for s in Task.TRANSITIONS[Task.Status(obj.status)]), key=order.index)


class TransitionSerializer(serializers.Serializer):
    to = serializers.CharField()

    def __init__(self, *args, choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._choices = choices or []

    def validate_to(self, value):
        if value not in self._choices:
            raise serializers.ValidationError(f"to は {', '.join(self._choices)} のいずれかを指定してください。")
        return value


# --- 版 ---
class VersionSerializer(serializers.ModelSerializer):
    task = VisibleTaskField()
    task_name = serializers.CharField(source="task.step.name", read_only=True)
    entity = serializers.IntegerField(source="task.entity_id", read_only=True)
    entity_name = serializers.CharField(source="task.entity.name", read_only=True)
    project_code = serializers.CharField(source="task.entity.project.code", read_only=True)
    thumbnail = serializers.CharField(source="thumb", required=False, allow_blank=True, max_length=500)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = [
            "id", "task", "task_name", "entity", "entity_name", "project_code",
            "number", "status", "status_label", "file_ref", "thumbnail", "comment", "dcc",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["number", "created_by", "created_at", "updated_at"]

    def validate_status(self, value):
        # 作成時に選べるのは「作成中」「提出済み」のみ。承認・却下は transition(レビュアーのみ)。
        if value not in {Version.Status.DRAFT, Version.Status.SUBMITTED}:
            raise serializers.ValidationError("作成時に指定できるのは draft / submitted のみです。")
        return value

    def validate_dcc(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("dcc はオブジェクトで指定してください。")
        return value

    def get_created_by_name(self, obj):
        return display_name(obj.created_by)


# --- ノート ---
class NoteSerializer(serializers.ModelSerializer):
    target_type = serializers.SerializerMethodField()
    target_id = serializers.IntegerField(source="object_id", read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ["id", "target_type", "target_id", "body", "author", "author_name", "created_at"]
        read_only_fields = fields

    def get_target_type(self, obj):
        return Note.target_type_name(obj.content_type)

    def get_author_name(self, obj):
        return display_name(obj.author)


class NoteCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=list(Note.TARGET_MODELS))
    target_id = serializers.IntegerField(min_value=1)
    body = serializers.CharField(max_length=5000)

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("本文を入力してください。")
        return value


# --- 連携データ(参照用・読み取り専用) ---
class QualityReportSerializer(serializers.ModelSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)

    class Meta:
        model = QualityReport
        fields = [
            "id", "project", "project_code", "entity", "scan_run_id", "asset_path",
            "defects", "scanned_at", "ingested_at",
        ]
        read_only_fields = fields


class VisualResultSerializer(serializers.ModelSerializer):
    verdict_label = serializers.CharField(source="get_verdict_display", read_only=True)
    version_number = serializers.IntegerField(source="version.number", read_only=True)

    class Meta:
        model = VisualResult
        fields = [
            "id", "version", "version_number", "run_id", "verdict", "verdict_label",
            "diff_ratio", "captured_at", "conditions", "ingested_at",
        ]
        read_only_fields = fields


# --- 取り込み(入力) ---
class AwareDateTimeField(serializers.DateTimeField):
    """タイムゾーン付きだけを受け付ける。無いと取り込み元と時刻がずれても気づけないため、黙って補わない。"""

    def enforce_timezone(self, value):
        if timezone.is_naive(value):
            raise serializers.ValidationError("タイムゾーン付きで指定してください(例: 2026-10-11T09:00:00+09:00 または ...Z)。")
        return super().enforce_timezone(value)


class QualityRowSerializer(serializers.Serializer):
    asset_path = serializers.CharField(max_length=500)
    defects = serializers.IntegerField(min_value=0)

    def validate_asset_path(self, value):
        if not normalize_path(value):
            raise serializers.ValidationError("アセットのパスが空です。")
        return value


class QualityIngestSerializer(serializers.Serializer):
    project = serializers.CharField(max_length=32)
    scan_run_id = serializers.IntegerField(min_value=0)
    scanned_at = AwareDateTimeField()
    results = QualityRowSerializer(many=True, max_length=50000)

    def validate_project(self, value):
        try:
            return Project.objects.get(code=value)
        except Project.DoesNotExist:
            raise serializers.ValidationError("存在しないプロジェクトコードです。")


class VisualIngestSerializer(serializers.Serializer):
    run_id = serializers.CharField(max_length=64)
    version = serializers.IntegerField(min_value=1)
    verdict = serializers.ChoiceField(choices=VisualResult.Verdict.choices)
    diff_ratio = serializers.FloatField(min_value=0, max_value=1)  # 0〜1 の割合(%ではない)
    captured_at = AwareDateTimeField()
    conditions = serializers.DictField(required=False, default=dict)

    def validate_version(self, value):
        try:
            return Version.objects.get(pk=value)
        except Version.DoesNotExist:
            raise serializers.ValidationError("存在しない版です。")
