"""状態遷移の「全遷移の表」と、権限・条件のテスト(設計書 3.3 / 検証チェックリスト)。"""

import pytest

from tracker.errors import Forbidden, InvalidTransition, RuleViolation
from tracker.models import Task

from .factories import VersionFactory

S = Task.Status

ALLOWED = {
    (S.TODO, S.IN_PROGRESS),
    (S.IN_PROGRESS, S.REVIEW),
    (S.REVIEW, S.IN_PROGRESS),
    (S.REVIEW, S.DONE),
    (S.DONE, S.IN_PROGRESS),
}
ALL_PAIRS = [(a, b) for a in S for b in S]


@pytest.mark.parametrize("src,dst", ALL_PAIRS)
def test_transition_table_matches_design(task, reviewer, src, dst):
    """4x4 の全組み合わせ。表にあるものだけ通り、他は InvalidTransition。"""
    task.status = src
    task.save()
    VersionFactory.create(task)  # 「完了」の条件(版が1つ以上)を満たしておく

    if (src, dst) in ALLOWED:
        task.transition_to(dst, reviewer)
        task.refresh_from_db()
        assert task.status == dst
    else:
        with pytest.raises(InvalidTransition):
            task.transition_to(dst, reviewer)
        task.refresh_from_db()
        assert task.status == src


def test_artist_can_submit_for_review(task, artist):
    task.status = S.IN_PROGRESS
    task.save()
    task.transition_to(S.REVIEW, artist)
    assert task.status == S.REVIEW


def test_only_reviewer_can_approve(task, artist, reviewer):
    task.status = S.REVIEW
    task.save()
    VersionFactory.create(task)
    with pytest.raises(Forbidden):
        task.transition_to(S.DONE, artist)
    task.refresh_from_db()
    assert task.status == S.REVIEW
    task.transition_to(S.DONE, reviewer)
    assert task.status == S.DONE


def test_staff_without_reviewer_role_cannot_approve(task, make_user):
    """管理者(is_staff)でも、承認はレビュアーの役割を持つ人だけ(設計書 3.3)。"""
    staff = make_user(None, is_staff=True)
    task.status = S.REVIEW
    task.save()
    VersionFactory.create(task)
    with pytest.raises(Forbidden):
        task.transition_to(S.DONE, staff)


def test_viewer_and_outsider_cannot_transition(task, viewer, outsider):
    for user in (viewer, outsider):
        with pytest.raises(Forbidden):
            task.transition_to(S.IN_PROGRESS, user)


def test_done_requires_at_least_one_version(task, reviewer):
    task.status = S.REVIEW
    task.save()
    with pytest.raises(RuleViolation) as e:
        task.transition_to(S.DONE, reviewer)
    assert e.value.code == "version_required"


def test_version_rule_can_be_disabled(task, reviewer, settings):
    settings.REQUIRE_VERSION_FOR_COMPLETION = False
    task.status = S.REVIEW
    task.save()
    task.transition_to(S.DONE, reviewer)
    assert task.status == S.DONE
