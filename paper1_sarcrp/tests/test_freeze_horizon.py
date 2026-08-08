from sarcrp.schemas import Action, Plan
from sarcrp.freeze_horizon import split_plan


def make_plan(n):
    actions = [Action(action_id=f"a{i}", step_index=i, type="RELOCATE", container=f"C{i}",
                       source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=i)
               for i in range(n)]
    return Plan(plan_id="p", created_at=0, source="t", actions=actions)


def test_split_respects_h_f_default_3():
    plan = make_plan(6)
    frozen, tail = split_plan(plan, h_f=3)
    assert [a.step_index for a in frozen.actions] == [0, 1, 2]
    assert [a.step_index for a in tail.actions] == [3, 4, 5]


def test_split_with_h_f_larger_than_plan_freezes_everything():
    plan = make_plan(2)
    frozen, tail = split_plan(plan, h_f=5)
    assert len(frozen.actions) == 2
    assert len(tail.actions) == 0


def test_split_with_h_f_zero_freezes_nothing():
    plan = make_plan(3)
    frozen, tail = split_plan(plan, h_f=0)
    assert len(frozen.actions) == 0
    assert len(tail.actions) == 3
