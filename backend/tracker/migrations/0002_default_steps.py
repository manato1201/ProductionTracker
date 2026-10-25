from django.db import migrations

DEFAULT_STEPS = [
    ("model", "モデリング"),
    ("texture", "テクスチャ"),
    ("rig", "リグ"),
    ("anim", "アニメーション"),
    ("fx", "FX"),
    ("light", "ライティング"),
]


def add_steps(apps, schema_editor):
    Step = apps.get_model("tracker", "Step")
    for order, (code, name) in enumerate(DEFAULT_STEPS, start=1):
        Step.objects.get_or_create(code=code, defaults={"name": name, "order": order * 10})


def remove_steps(apps, schema_editor):
    Step = apps.get_model("tracker", "Step")
    # 既にタスクが使っている工程は消さない(PROTECT)
    Step.objects.filter(code__in=[c for c, _ in DEFAULT_STEPS], tasks__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("tracker", "0001_initial")]
    operations = [migrations.RunPython(add_steps, remove_steps)]
