from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from . import serializers as s
from .errors import Forbidden, IdempotencyConflict
from .models import (
    Note,
    ProjectMember,
    QualityReport,
    Step,
    Task,
    Version,
    VisualResult,
)
from .permissions import (
    require_write,
    visible_entities,
    visible_projects,
    visible_tasks,
    visible_versions,
)


# --- クエリパラメータの読み取り(不正値は 400) ---
def int_param(request, name):
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except ValueError:
        raise serializers.ValidationError({name: "整数で指定してください。"})


def project_q(request, prefix=""):
    """`?project=` は id でもコードでも指定できる。"""
    raw = request.query_params.get("project")
    if not raw:
        return Q()
    if raw.isdigit():
        return Q(**{f"{prefix}project_id": int(raw)})
    return Q(**{f"{prefix}project__code": raw})


def apply_ordering(request, queryset, allowed: dict, default):
    """`?ordering=` は許可リストのみ。同順位は id で固定して、ページ送りがぶれないようにする。"""
    key = request.query_params.get("ordering") or default
    expressions = allowed.get(key)
    if expressions is None:
        raise serializers.ValidationError({"ordering": f"{', '.join(allowed)} のいずれかを指定してください。"})
    return queryset.order_by(*expressions, "-id" if key.startswith("-") else "id")


# --- プロジェクト ---
class ProjectViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = s.ProjectSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    lookup_value_regex = "[^/]+"  # id でもコードでも引ける

    ORDERING = {
        "-updated_at": ["-updated_at"],
        "name": ["name"],
        "-name": ["-name"],
        "due": [F("due").asc(nulls_last=True)],
        "-due": [F("due").desc(nulls_last=True)],
        "code": ["code"],
    }

    def get_queryset(self):
        user = self.request.user
        count = lambda status: Count(  # noqa: E731
            "entities__tasks", filter=Q(entities__tasks__status=status), distinct=True
        )
        role = ProjectMember.objects.filter(project=OuterRef("pk"), user=user).values("role")[:1]
        qs = visible_projects(user).annotate(
            n_todo=count("todo"),
            n_in_progress=count("in_progress"),
            n_review=count("review"),
            n_done=count("done"),
            my_role=Subquery(role),
        )
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        if self.action == "list":
            qs = apply_ordering(self.request, qs, self.ORDERING, "-updated_at")
        return qs

    def get_object(self):
        lookup = self.kwargs["pk"]
        return self._get({"pk": int(lookup)} if lookup.isdigit() else {"code": lookup})

    def _get(self, flt):
        return get_object_or_404(self.get_queryset(), **flt)

    def perform_create(self, serializer):
        with transaction.atomic():
            project = serializer.save()
            # 作成者は、そのプロジェクトのレビュアーになる(でないと自分で承認も編集もできない)
            ProjectMember.objects.create(project=project, user=self.request.user, role=ProjectMember.Role.REVIEWER)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        fresh = self._get({"pk": serializer.instance.pk})  # 件数・役割の annotate 付きで返す
        return Response(self.get_serializer(fresh).data, status=201)

    def partial_update(self, request, *args, **kwargs):
        project = self.get_object()
        if not (request.user.is_staff or project.can_review(request.user)):
            raise Forbidden("プロジェクトを更新できるのはレビュアーのみです。")
        serializer = self.get_serializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(self._get({"pk": project.pk})).data)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        project = self.get_object()
        qs = project.members.select_related("user").order_by("user__username")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(s.MemberSerializer(page, many=True).data)


# --- 工程 ---
class StepViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Step.objects.all()
    serializer_class = s.StepSerializer


# --- アセット ---
class EntityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = s.EntitySerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    ORDERING = {"name": ["name"], "-name": ["-name"], "-updated_at": ["-updated_at"]}

    def get_queryset(self):
        qs = visible_entities(self.request.user).select_related("project").annotate(
            task_count=Count("tasks", distinct=True),
            done_count=Count("tasks", filter=Q(tasks__status="done"), distinct=True),
        )
        req = self.request
        qs = qs.filter(project_q(req))
        for name in ("kind", "status"):
            if req.query_params.get(name):
                qs = qs.filter(**{name: req.query_params[name]})
        if req.query_params.get("q"):
            qs = qs.filter(name__icontains=req.query_params["q"])
        if self.action == "list":
            qs = apply_ordering(req, qs, self.ORDERING, "name")
        return qs

    def perform_create(self, serializer):
        require_write(self.request.user, serializer.validated_data["project"])
        serializer.save()

    def perform_update(self, serializer):
        require_write(self.request.user, serializer.instance.project)
        serializer.save()


# --- タスク ---
TASK_STATUS_ORDER = {"todo": 0, "in_progress": 1, "review": 2, "done": 3}


class TaskViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = s.TaskSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    ORDERING = {
        "-updated_at": ["-updated_at"],
        "due": [F("due").asc(nulls_last=True)],
        "-due": [F("due").desc(nulls_last=True)],
        "status": ["status"],
    }

    def get_queryset(self):
        req = self.request
        qs = (
            visible_tasks(req.user)
            .select_related("entity__project", "step", "assignee")
            .annotate(version_count=Count("versions", distinct=True))
        )
        qs = qs.filter(project_q(req, "entity__"))
        entity = int_param(req, "entity")
        if entity is not None:
            qs = qs.filter(entity_id=entity)

        assignee = req.query_params.get("assignee")
        if assignee == "me":
            qs = qs.filter(assignee=req.user)
        elif assignee:
            qs = qs.filter(assignee_id=int_param(req, "assignee"))

        statuses = [v for v in req.query_params.get("status", "").split(",") if v]
        if statuses:
            invalid = [v for v in statuses if v not in Task.Status.values]
            if invalid:
                raise serializers.ValidationError({"status": f"不正な状態: {', '.join(invalid)}"})
            qs = qs.filter(status__in=statuses)

        priority = req.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)
        if req.query_params.get("overdue") in {"1", "true"}:
            qs = qs.filter(due__lt=timezone.localdate()).exclude(status="done")
        q = req.query_params.get("q")
        if q:
            qs = qs.filter(Q(entity__name__icontains=q) | Q(step__name__icontains=q))
        if self.action == "list":
            qs = apply_ordering(req, qs, self.ORDERING, "-updated_at")
        return qs

    def _fresh(self, pk):
        return self.get_serializer(self.get_queryset().get(pk=pk)).data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_write(request.user, serializer.validated_data["entity"].project)
        task = serializer.save()
        return Response(self._fresh(task.pk), status=201)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        require_write(request.user, task.project)
        serializer = self.get_serializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self._fresh(task.pk))

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        """状態遷移。不正な遷移は 409、権限が無ければ 403(ルールは Task.transition_to)。"""
        task = self.get_object()
        body = s.TransitionSerializer(data=request.data, choices=Task.Status.values)
        body.is_valid(raise_exception=True)
        with transaction.atomic():
            locked = Task.objects.select_for_update().select_related("entity__project", "step").get(pk=task.pk)
            locked.transition_to(body.validated_data["to"], request.user)
        return Response(self._fresh(task.pk))


# --- 版 ---
class VersionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = s.VersionSerializer
    ORDERING = {"-created_at": ["-created_at"], "created_at": ["created_at"]}

    def get_queryset(self):
        req = self.request
        qs = visible_versions(req.user).select_related("task__step", "task__entity__project", "created_by")
        qs = qs.filter(project_q(req, "task__entity__"))
        task, entity = int_param(req, "task"), int_param(req, "entity")
        if task is not None:
            qs = qs.filter(task_id=task)
        if entity is not None:
            qs = qs.filter(task__entity_id=entity)
        if req.query_params.get("status"):
            qs = qs.filter(status=req.query_params["status"])
        if self.action == "list":
            qs = apply_ordering(req, qs, self.ORDERING, "-created_at")
        return qs

    def create(self, request, *args, **kwargs):
        """版の登録。`Idempotency-Key` が同じ再送は、新規作成せず同じ版を返す(設計書 Phase 8)。"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        task = data.pop("task")
        require_write(request.user, task.project)

        key = request.headers.get("Idempotency-Key") or None
        if key is not None and len(key) > 200:
            raise serializers.ValidationError({"Idempotency-Key": "200 文字以内にしてください。"})

        def replay():
            existing = Version.objects.filter(created_by=request.user, idempotency_key=key).first()
            if existing is None:
                return None
            if existing.task_id != task.pk:
                raise IdempotencyConflict("同じ Idempotency-Key が別のタスクの版に使われています。")
            return Response(self.get_serializer(existing).data, status=200)

        if key:
            response = replay()
            if response is not None:
                return response
        try:
            version = Version.create_for_task(task, created_by=request.user, idempotency_key=key, **data)
        except IntegrityError:
            # 同じ鍵の同時送信に負けた場合
            response = replay() if key else None
            if response is None:
                raise
            return response
        return Response(self.get_serializer(version).data, status=201)

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        version = self.get_object()
        body = s.TransitionSerializer(data=request.data, choices=Version.Status.values)
        body.is_valid(raise_exception=True)
        with transaction.atomic():
            locked = Version.objects.select_for_update().select_related("task__entity__project").get(pk=version.pk)
            locked.transition_to(body.validated_data["to"], request.user)
        return Response(self.get_serializer(self.get_queryset().get(pk=version.pk)).data)


# --- ノート ---
def resolve_note_target(user, target_type: str, target_id: int):
    """ノートの対象(entity / task / version)を、利用者から見える範囲で引く。"""
    queryset = {
        "entity": visible_entities(user),
        "task": visible_tasks(user),
        "version": visible_versions(user),
    }[target_type]
    return queryset.filter(pk=target_id).first()


class NoteViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = s.NoteSerializer

    def get_queryset(self):
        req = self.request
        target_type = req.query_params.get("target_type")
        target_id = int_param(req, "target_id")
        if target_type not in Note.TARGET_MODELS or target_id is None:
            raise serializers.ValidationError(
                {"target_type": "target_type(entity / task / version)と target_id を指定してください。"}
            )
        if resolve_note_target(req.user, target_type, target_id) is None:
            raise NotFound()
        ct = ContentType.objects.get_for_model(Note.TARGET_MODELS[target_type])
        return (
            Note.objects.filter(content_type=ct, object_id=target_id)
            .select_related("author", "content_type")
            .order_by("-created_at", "-id")
        )

    def create(self, request, *args, **kwargs):
        body = s.NoteCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        target = resolve_note_target(request.user, data["target_type"], data["target_id"])
        if target is None:
            raise serializers.ValidationError({"target_id": "対象が見つかりません。"})
        project = target.task.project if isinstance(target, Version) else target.project
        require_write(request.user, project)
        note = Note.objects.create(target=target, author=request.user, body=data["body"])
        return Response(s.NoteSerializer(note).data, status=201)


# --- 連携データの参照(読み取り専用) ---
class QualityReportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = s.QualityReportSerializer

    def get_queryset(self):
        req = self.request
        qs = QualityReport.objects.filter(project__in=visible_projects(req.user)).select_related("project")
        qs = qs.filter(project_q(req))
        entity = int_param(req, "entity")
        if entity is not None:
            qs = qs.filter(entity_id=entity)
        return qs.order_by("-scanned_at", "-scan_run_id", "asset_path", "id")


class VisualResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = s.VisualResultSerializer

    def get_queryset(self):
        req = self.request
        qs = VisualResult.objects.filter(version__in=visible_versions(req.user)).select_related("version")
        version, entity = int_param(req, "version"), int_param(req, "entity")
        if version is not None:
            qs = qs.filter(version_id=version)
        if entity is not None:
            qs = qs.filter(version__task__entity_id=entity)
        return qs.order_by("-captured_at", "-id")
