"""データモデルと状態遷移ルール。

状態の遷移ルール(設計書 3.3)はこのファイルの `Task.transition_to` / `Version.transition_to`
に集約する。API と UI は、その結果を表示するだけにする。
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import Max, Q
from django.db.models.functions import Lower

from .errors import Forbidden, InvalidTransition, RuleViolation

code_validator = RegexValidator(
    r"^[A-Za-z][A-Za-z0-9_-]*$",
    "英字で始まり、英数字・_・- のみ使えます(URL に使うため)。",
)


class Project(models.Model):
    code = models.CharField("コード", max_length=32, unique=True, validators=[code_validator])
    name = models.CharField("名前", max_length=120)
    start = models.DateField("開始日", null=True, blank=True)
    due = models.DateField("期日", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "プロジェクト"
        verbose_name_plural = "プロジェクト"
        constraints = [
            # `demo` と `DEMO` を別物にしない(URL・取り込みの指定が曖昧になるため)
            models.UniqueConstraint(Lower("code"), name="uniq_project_code_ci"),
        ]

    def __str__(self):
        return f"{self.code} {self.name}"

    # --- 役割(ProjectMember.role)。管理者権限は Django 標準の is_staff ---
    # 権限の判定はここ(can_write_as / can_review_as)だけに置く。シリアライザも同じ関数を使う。
    @staticmethod
    def can_write_as(role: str | None, is_staff: bool) -> bool:
        return bool(is_staff or role in ProjectMember.WRITER_ROLES)

    @staticmethod
    def can_review_as(role: str | None) -> bool:
        """承認できるのは、プロジェクトの「レビュアー」の役割を持つユーザーのみ(is_staff でも不可)。"""
        return role == ProjectMember.Role.REVIEWER

    def role_for(self, user) -> str | None:
        if user is None or not getattr(user, "is_authenticated", False) or user.pk is None:
            return None
        return self.members.filter(user=user).values_list("role", flat=True).first()

    def can_write(self, user) -> bool:
        return self.can_write_as(self.role_for(user), getattr(user, "is_staff", False))

    def can_review(self, user) -> bool:
        return self.can_review_as(self.role_for(user))


class ProjectMember(models.Model):
    class Role(models.TextChoices):
        REVIEWER = "reviewer", "レビュアー"
        ARTIST = "artist", "アーティスト"
        VIEWER = "viewer", "閲覧者"

    WRITER_ROLES = frozenset({"reviewer", "artist"})  # 編集できる役割(viewer は閲覧のみ)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField("役割", max_length=16, choices=Role.choices, default=Role.ARTIST)

    class Meta:
        verbose_name = "プロジェクトメンバー"
        verbose_name_plural = "プロジェクトメンバー"
        constraints = [models.UniqueConstraint(fields=["project", "user"], name="uniq_member_per_project")]

    def __str__(self):
        return f"{self.project.code}:{self.user} ({self.role})"


class Step(models.Model):
    """工程(モデリング・リグ・FX など)。"""

    code = models.SlugField("コード", max_length=32, unique=True)
    name = models.CharField("名前", max_length=64)
    order = models.PositiveSmallIntegerField("並び順", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "工程"
        verbose_name_plural = "工程"

    def __str__(self):
        return self.name


class Entity(models.Model):
    """ShotGrid の Asset / Shot。まずは asset のみ実装する(kind は将来の shot 用に残す)。"""

    class Kind(models.TextChoices):
        ASSET = "asset", "アセット"
        SHOT = "shot", "ショット"

    class Status(models.TextChoices):
        ACTIVE = "active", "進行中"
        ON_HOLD = "on_hold", "保留"
        FINAL = "final", "確定"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="entities")
    name = models.CharField("名前", max_length=120)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.ASSET)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    # AssetDataInsightSuite のアセットパスとの突き合わせ用(前方一致)。区切りは / に正規化して保存する
    path = models.CharField("パス", max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = GenericRelation("Note")  # 削除時にノートも道連れにする(孤児を残さない)

    class Meta:
        verbose_name = "アセット"
        verbose_name_plural = "アセット"
        constraints = [models.UniqueConstraint(fields=["project", "kind", "name"], name="uniq_entity_name")]

    def __str__(self):
        return f"{self.project.code}/{self.name}"


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "未着手"
        IN_PROGRESS = "in_progress", "進行中"
        REVIEW = "review", "レビュー待ち"
        DONE = "done", "完了"

    class Priority(models.TextChoices):
        LOW = "low", "低"
        NORMAL = "normal", "中"
        HIGH = "high", "高"
        URGENT = "urgent", "緊急"

    # 遷移表(設計書 3.3)。ここに無い組み合わせは 409。
    TRANSITIONS = {
        Status.TODO: frozenset({Status.IN_PROGRESS}),
        Status.IN_PROGRESS: frozenset({Status.REVIEW}),
        Status.REVIEW: frozenset({Status.IN_PROGRESS, Status.DONE}),  # 差し戻し / 承認
        Status.DONE: frozenset({Status.IN_PROGRESS}),  # 再開
    }

    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="tasks")
    step = models.ForeignKey(Step, on_delete=models.PROTECT, related_name="tasks")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    due = models.DateField("期日", null=True, blank=True)
    estimate_h = models.FloatField("見積(時間)", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = GenericRelation("Note")

    class Meta:
        verbose_name = "タスク"
        verbose_name_plural = "タスク"
        constraints = [
            models.UniqueConstraint(fields=["entity", "step"], name="uniq_task_per_step"),
            models.CheckConstraint(
                condition=Q(estimate_h__isnull=True) | Q(estimate_h__gte=0), name="task_estimate_non_negative"
            ),
        ]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["due"])]

    def __str__(self):
        return f"{self.entity.name} / {self.step.name}"

    @property
    def project(self) -> Project:
        return self.entity.project

    def transition_to(self, to: str, user) -> None:
        """状態遷移。呼び出し側で行ロック(select_for_update)と atomic を用意すること。"""
        current = self.Status(self.status)
        to = self.Status(to)
        if to not in self.TRANSITIONS[current]:
            raise InvalidTransition(f"「{current.label}」から「{to.label}」へは移行できません。")

        project = self.project
        if not project.can_write(user):
            raise Forbidden("このプロジェクトのタスクを操作する権限がありません。")
        if current == self.Status.REVIEW and to == self.Status.DONE and not project.can_review(user):
            raise Forbidden("承認できるのは、このプロジェクトのレビュアーのみです。")
        if (
            to == self.Status.DONE
            and settings.REQUIRE_VERSION_FOR_COMPLETION
            and not self.versions.exists()
        ):
            raise RuleViolation("「完了」にするには、版が1つ以上必要です。", code="version_required")

        self.status = to
        self.save(update_fields=["status", "updated_at"])


class Version(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "作成中"
        SUBMITTED = "submitted", "提出済み"
        APPROVED = "approved", "承認"
        REJECTED = "rejected", "却下"

    # タスクの遷移(Task.TRANSITIONS)とは独立。
    TRANSITIONS = {
        Status.DRAFT: frozenset({Status.SUBMITTED}),
        Status.SUBMITTED: frozenset({Status.APPROVED, Status.REJECTED}),
        Status.APPROVED: frozenset(),
        Status.REJECTED: frozenset({Status.DRAFT}),  # 直して作り直す
    }
    REVIEWER_ONLY = frozenset({Status.APPROVED, Status.REJECTED})

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField("版番号")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    file_ref = models.CharField("ファイルの場所", max_length=500)
    thumb = models.CharField("サムネイル(登録済みの画像の場所)", max_length=500, blank=True)
    comment = models.TextField(blank=True)
    dcc = models.JSONField("DCC 情報", default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="versions"
    )
    # Publish API の再送で重複させないための鍵(ユーザーごとに一意)
    idempotency_key = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = GenericRelation("Note")

    class Meta:
        verbose_name = "版"
        verbose_name_plural = "版"
        constraints = [
            models.UniqueConstraint(fields=["task", "number"], name="uniq_version_number"),
            models.UniqueConstraint(
                fields=["created_by", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="uniq_version_idempotency",
            ),
        ]

    def __str__(self):
        return f"{self.task} v{self.number:03d}"

    @classmethod
    def create_for_task(cls, task: Task, **fields) -> "Version":
        """版番号をタスク内で連番にして作る。タスク行をロックして同時作成を直列化する。"""
        with transaction.atomic():
            Task.objects.select_for_update().get(pk=task.pk)
            last = cls.objects.filter(task=task).aggregate(m=Max("number"))["m"] or 0
            return cls.objects.create(task=task, number=last + 1, **fields)

    def transition_to(self, to: str, user) -> None:
        current = self.Status(self.status)
        to = self.Status(to)
        if to not in self.TRANSITIONS[current]:
            raise InvalidTransition(f"版の状態を「{current.label}」から「{to.label}」へは変更できません。")
        project = self.task.project
        if not project.can_write(user):
            raise Forbidden("このプロジェクトの版を操作する権限がありません。")
        if to in self.REVIEWER_ONLY and not project.can_review(user):
            raise Forbidden("版を承認・却下できるのは、このプロジェクトのレビュアーのみです。")

        self.status = to
        self.save(update_fields=["status", "updated_at"])

        # 「却下」でタスクを自動で差し戻すかは設定(既定は動かさない)
        if to == self.Status.REJECTED and settings.RETURN_TASK_ON_VERSION_REJECT:
            task = self.task
            if task.status == Task.Status.REVIEW:
                task.status = Task.Status.IN_PROGRESS
                task.save(update_fields=["status", "updated_at"])


class Note(models.Model):
    """コメント。対象は Entity / Task / Version の3種に限定(GenericForeignKey)。"""

    TARGET_MODELS = {"entity": Entity, "task": Task, "version": Version}

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="notes"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ノート"
        verbose_name_plural = "ノート"
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"Note#{self.pk} on {self.content_type_id}:{self.object_id}"

    @classmethod
    def target_type_name(cls, content_type: ContentType) -> str | None:
        for name, model in cls.TARGET_MODELS.items():
            if content_type.model_class() is model:
                return name
        return None


class QualityReport(models.Model):
    """AssetDataInsightSuite の結果(参照用・読み取り専用)。(project, scan_run_id) 単位で置き換える。"""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="quality_reports")
    entity = models.ForeignKey(
        Entity, null=True, blank=True, on_delete=models.SET_NULL, related_name="quality_reports"
    )
    scan_run_id = models.BigIntegerField()
    asset_path = models.CharField(max_length=500)
    defects = models.PositiveBigIntegerField()  # 同じパスの行を合算するので bigint
    scanned_at = models.DateTimeField()
    ingested_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "品質レポート"
        verbose_name_plural = "品質レポート"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "scan_run_id", "asset_path"], name="uniq_quality_row"
            )
        ]
        indexes = [models.Index(fields=["entity", "-scanned_at"])]


class VisualResult(models.Model):
    """VisualRegressionQATool の評価結果(参照用・読み取り専用)。(run_id, version) で一意。"""

    class Verdict(models.TextChoices):
        PASS = "pass", "合格"
        FAIL = "fail", "不合格"

    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="visual_results")
    run_id = models.CharField(max_length=64)
    verdict = models.CharField(max_length=8, choices=Verdict.choices)
    diff_ratio = models.FloatField()
    captured_at = models.DateTimeField()
    # 撮影条件(解像度・固定時刻・シード)も保存し、画面に固定表示する
    conditions = models.JSONField(default=dict, blank=True)
    ingested_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "画面差分の結果"
        verbose_name_plural = "画面差分の結果"
        constraints = [
            models.UniqueConstraint(fields=["run_id", "version"], name="uniq_visual_run"),
            models.CheckConstraint(condition=Q(diff_ratio__gte=0) & Q(diff_ratio__lte=1), name="visual_diff_ratio_0_1"),
        ]
