import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from run_crp_rl_native_cost_comparison import (  # noqa: E402
    parse_lee_shin_tensor, plan_to_moves, replay_native_cost,
)
from sarcrp.crp_rl_adapter import CRP_RL_ROOT  # noqa: E402
from sarcrp.schemas import Action  # noqa: E402


def make_action(step_index, type_, source_stack=None, dest_stack=None):
    return Action(
        action_id=f"a{step_index}", step_index=step_index, type=type_, container=f"C{step_index}",
        source_stack=source_stack, dest_stack=dest_stack, commit_status="planned", planned_time=step_index,
    )


class FakePlan:
    def __init__(self, actions):
        self.actions = actions


def test_plan_to_moves_extracts_relocate_actions_in_step_order_skipping_retrieve():
    stack_id_to_bay = {"S1": 0, "S2": 1, "S3": 2}
    # Deliberately out of step_index order and interleaved with RETRIEVE,
    # to check both the sort and the type filter.
    plan = FakePlan([
        make_action(2, "RETRIEVE"),
        make_action(0, "RELOCATE", source_stack="S1", dest_stack="S2"),
        make_action(1, "RELOCATE", source_stack="S2", dest_stack="S3"),
    ])
    assert plan_to_moves(plan, stack_id_to_bay) == [(0, 1), (1, 2)]


def test_parse_lee_shin_tensor_matches_hand_built_matrix(tmp_path):
    # 2 bays x 1 row x 2 tiers. Bay1/row1: rank1 bottom, rank3 top (each
    # rank listed twice, matching the real Lee/Shin file format that
    # parse_container_file also de-duplicates). Bay2/row1: rank2 only.
    file_path = tmp_path / "toy_instance.txt"
    file_path.write_text("header line, ignored by the parser\n1 1 2 1 1 3 3\n2 1 1 2 2\n")
    x = parse_lee_shin_tensor(file_path, n_bays=2, n_rows=1, n_tiers=2)
    assert tuple(x.shape) == (1, 2, 1, 2)
    assert x[0, 0, 0, 0].item() == 1.0
    assert x[0, 0, 0, 1].item() == 3.0
    assert x[0, 1, 0, 0].item() == 2.0
    assert x[0, 1, 0, 1].item() == 0.0  # padded


@pytest.mark.skipif(not CRP_RL_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_replay_native_cost_matches_hand_computed_travel_time():
    # Hand-derived from CRP_RL's own Env cost formulas (t_pd=30, t_acc=40,
    # t_bay=3.5, t_row=1.2): 2 bays, 1 row, 2 tiers. Bay1=[rank1 bottom,
    # rank3 top] (rank1 buried -- nothing auto-retrievable yet, clear()=0),
    # Bay2=[rank2]. Relocating Bay1's top (rank3) to Bay2 is a cross-bay
    # move (t_acc + 1*t_bay + t_pd = 73.5); that exposes rank1 at Bay1,
    # which auto-retrieves (cross-bay access from Bay2 back to Bay1: t_acc
    # + 1*t_bay + 0*t_row(dest) + 1*t_row(target_row) + t_pd = 74.7).
    # Rank2 ends up buried under the just-moved rank3 in Bay2, so nothing
    # else auto-retrieves. Total = 73.5 + 74.7 = 148.2.
    import torch
    from sarcrp.crp_rl_adapter import _ensure_crp_rl_on_path

    _ensure_crp_rl_on_path()
    x = torch.tensor([[[[1.0, 3.0]], [[2.0, 0.0]]]])  # shape (1, 2, 1, 2)
    cost = replay_native_cost(x, moves=[(0, 1)], device="cpu")
    assert cost == pytest.approx(148.2)


@pytest.mark.skipif(not CRP_RL_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_replay_native_cost_with_no_moves_only_charges_the_initial_clear():
    # Bay1=[rank1] only (already on top -- auto-retrieves for free relative
    # to any relocation), Bay2=[rank2] only: with the ranks laid out so
    # both are immediately retrievable in the initial clear(), an empty
    # move list should still charge exactly the two retrieve costs (no
    # relocation cost at all).
    import torch
    from sarcrp.crp_rl_adapter import _ensure_crp_rl_on_path

    _ensure_crp_rl_on_path()
    x = torch.tensor([[[[1.0]], [[2.0]]]])  # shape (1, 2, 1, 1)
    cost = replay_native_cost(x, moves=[], device="cpu")
    assert cost > 0.0
    # Both containers retrieve from bay1 then bay2, cascading in one clear() loop.
    from env.env import Env  # noqa: E402
    env = Env(torch.device("cpu"), x.clone())
    env.find_target_stack()
    expected = env.clear()
    assert cost == pytest.approx(float(expected.sum().item()))
