from django.contrib import admin

from .models import (
    AuditEvent,
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


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "start", "due"]
    search_fields = ["code", "name"]
    inlines = [ProjectMemberInline]


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "order"]
    ordering = ["order"]


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "kind", "status", "path"]
    list_filter = ["project", "kind", "status"]
    search_fields = ["name", "path"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["entity", "step", "status", "priority", "assignee", "due"]
    list_filter = ["status", "priority", "step", "entity__project"]
    search_fields = ["entity__name"]
    raw_id_fields = ["entity", "assignee"]


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ["task", "number", "status", "file_ref", "created_by", "created_at"]
    list_filter = ["status", "task__entity__project"]
    raw_id_fields = ["task", "created_by"]
    readonly_fields = ["idempotency_key"]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["id", "content_type", "object_id", "author", "created_at"]
    raw_id_fields = ["author"]


@admin.register(QualityReport)
class QualityReportAdmin(admin.ModelAdmin):
    list_display = ["project", "scan_run_id", "asset_path", "defects", "entity", "scanned_at"]
    list_filter = ["project"]
    search_fields = ["asset_path"]


@admin.register(VisualResult)
class VisualResultAdmin(admin.ModelAdmin):
    list_display = ["version", "run_id", "verdict", "diff_ratio", "captured_at"]
    list_filter = ["verdict"]


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """監査ログは見るだけ(追加・変更・削除は管理画面からもできない)。"""

    list_display = ["created_at", "project_code", "actor_name", "action", "target_type", "target_id"]
    list_filter = ["action", "project_code"]
    search_fields = ["actor_name", "project_code"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
