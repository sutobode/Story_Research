"""Adapter wrapping the real trained CRP_RL model (Shin et al. 2026,
https://github.com/operagang/CRP_RL) behind a solve_crp-compatible
interface. The cloned repo is expected at paper1_sarcrp/external/CRP_RL
(gitignored -- see external/README.md for the clone command).

This module only reuses CRP_RL's *decisions* (which stack to relocate a
blocker to), not its own travel-time cost model -- the resulting Plan is
scored by this project's own objective.py, per spec 43."""

import argparse
import functools
import sys
from pathlib import Path

import torch

from sarcrp.schemas import Action, Plan, YardState

CRP_RL_ROOT = Path(__file__).resolve().parents[2] / "external" / "CRP_RL"


class CRPRLNotAvailable(RuntimeError):
    pass


def _ensure_crp_rl_on_path() -> None:
    if not CRP_RL_ROOT.is_dir():
        raise CRPRLNotAvailable(
            f"{CRP_RL_ROOT} not found -- clone it first (see paper1_sarcrp/external/README.md)"
        )
    root = str(CRP_RL_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def build_priority_tensor(yard_state: YardState, retrieval_queue: list[str]) -> torch.Tensor:
    """CRP_RL's env represents a yard as a (batch, n_bays, n_rows, max_tiers)
    tensor where a cell holds the container's 1-based retrieval rank (0 =
    empty). Our schema has no bay/row distinction, only a flat stack list,
    so each stack maps to one bay with n_rows fixed at 1. Tier index 0 =
    bottom in both conventions (verified against env.py's step()/clear()),
    so no reversal is needed."""
    n_bays = len(yard_state.stacks)
    max_tiers = max((s.max_tier for s in yard_state.stacks), default=1)
    rank = {c: i + 1 for i, c in enumerate(retrieval_queue)}

    x = torch.zeros(1, n_bays, 1, max_tiers)
    for bay, stack in enumerate(yard_state.stacks):
        for tier, container in enumerate(stack.containers):
            x[0, bay, 0, tier] = float(rank.get(container, len(retrieval_queue) + 1))
    return x


class _RecordingEnv:
    """Wraps CRP_RL's real Env, recording (source_stack_idx, dest_stack_idx)
    for every relocation `step()` call so the adapter can reconstruct an
    explicit action sequence. Delegates everything else unchanged."""

    def __init__(self, inner):
        self._inner = inner
        self.moves: list[tuple[int, int]] = []

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def step(self, dest_index, source_index=None, no_clear=False):
        src = source_index if source_index is not None else self._inner.target_stack[:, None]
        self.moves.append((int(src[0, 0].item()), int(dest_index[0, 0].item())))
        return self._inner.step(dest_index, source_index=source_index, no_clear=no_clear)


def _default_model_args(device: torch.device) -> argparse.Namespace:
    return argparse.Namespace(
        device=device, embed_dim=128, n_encode_layers=3, n_heads=8, ff_hidden=512,
        tanh_c=10, lstm=True, bay_embedding=True, online=False, online_known_num=None,
    )


def _load_model(model_path: str, device: torch.device):
    from model.model import Model

    args = _default_model_args(device)
    model = Model(args).to(device)
    state_dict = torch.load(str(CRP_RL_ROOT / model_path), map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    model.decoder.set_sampler("greedy")
    return model


@functools.lru_cache(maxsize=4)
def get_cached_model(model_path: str, device: str):
    """Loads the checkpoint once per (model_path, device) pair and reuses it
    -- solve_crp_via_crp_rl previously re-read the checkpoint from disk on
    every single call, which is fine for a one-off smoke test but would make
    any experiment calling it hundreds/thousands of times (Experiment-1
    scale) dominated by disk I/O instead of actual inference."""
    return _load_model(model_path, torch.device(device))


def _run_decode_recording_moves(model, x: torch.Tensor) -> list[tuple[int, int]]:
    import model.decoder as decoder_module

    original_env_cls = decoder_module.Env
    recorder_holder: dict = {}

    def _patched_env(device, x_arg, max_retrievals):
        wrapper = _RecordingEnv(original_env_cls(device, x_arg, max_retrievals))
        recorder_holder["env"] = wrapper
        return wrapper

    decoder_module.Env = _patched_env
    try:
        with torch.no_grad():
            model(x, None)
    finally:
        decoder_module.Env = original_env_cls

    return recorder_holder["env"].moves


def moves_to_plan(yard_state: YardState, retrieval_queue: list[str], moves: list[tuple[int, int]]) -> Plan:
    """Replays `moves` against a shadow copy of the stacks to emit RELOCATE
    actions, interleaved with RETRIEVE actions whenever the next-lowest-rank
    container reaches the top of its stack -- mirrors CRP_RL's Env.clear()
    auto-retrieval semantics (spec 43's Plan schema has explicit RETRIEVE
    actions; CRP_RL's env folds retrieval into an implicit loop)."""
    stack_ids = [s.id for s in yard_state.stacks]
    stacks = {s.id: list(s.containers) for s in yard_state.stacks}
    remaining_ranks = list(range(len(retrieval_queue)))
    actions: list[Action] = []
    step = 0

    def auto_retrieve():
        nonlocal step
        progressed = True
        while progressed and remaining_ranks:
            progressed = False
            next_container = retrieval_queue[remaining_ranks[0]]
            for sid in stack_ids:
                if stacks[sid] and stacks[sid][-1] == next_container:
                    stacks[sid].pop()
                    actions.append(Action(
                        action_id=f"crprl_{step:04d}", step_index=step, type="RETRIEVE",
                        container=next_container, source_stack=sid, dest_stack=None,
                        commit_status="planned", planned_time=step,
                    ))
                    step += 1
                    remaining_ranks.pop(0)
                    progressed = True
                    break

    auto_retrieve()
    for source_idx, dest_idx in moves:
        source_id, dest_id = stack_ids[source_idx], stack_ids[dest_idx]
        if not stacks[source_id]:
            continue
        container = stacks[source_id].pop()
        stacks[dest_id].append(container)
        actions.append(Action(
            action_id=f"crprl_{step:04d}", step_index=step, type="RELOCATE",
            container=container, source_stack=source_id, dest_stack=dest_id,
            commit_status="planned", planned_time=step,
        ))
        step += 1
        auto_retrieve()

    return Plan(plan_id="plan_crp_rl", created_at=yard_state.time_step, source="CRP_RL", actions=actions)


def solve_crp_via_crp_rl(
    yard_state: YardState,
    retrieval_queue: list[str],
    constraints: dict | None = None,
    time_limit_sec: float | None = None,
    model_path: str = "baselines/models/proposed/epoch(100).pt",
    device: str = "cpu",
) -> Plan:
    """Real CRP_RL inference: loads the pretrained checkpoint (cached after
    the first call, see get_cached_model), runs its decode loop on this
    single instance, and translates the resulting relocation sequence back
    into our Plan/Action schema (spec 43's solve_crp interface). `constraints`
    and `time_limit_sec` are accepted (both currently unused -- the model's
    decode loop has a fixed step bound, not a wall-clock budget) purely so
    this function is signature-compatible with solve_crp and can be passed
    as full_reoptimization's/replan's `solver` callable interchangeably."""
    _ensure_crp_rl_on_path()
    model = get_cached_model(model_path, device)
    x = build_priority_tensor(yard_state, retrieval_queue).to(torch.device(device))
    moves = _run_decode_recording_moves(model, x)
    return moves_to_plan(yard_state, retrieval_queue, moves)
