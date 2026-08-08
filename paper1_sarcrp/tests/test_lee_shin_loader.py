import pytest
from sarcrp.lee_shin_loader import LEE_SHIN_ROOT, find_lee_shin_file, load_lee_instance, parse_lee_shin_file


@pytest.fixture
def small_file(tmp_path):
    # A hand-written 3-line instance in CRP_RL's own on-disk format
    # (header, then one line per (bay,row): "bay row num_tiers c1 c1 c2 c2 ...").
    content = "T 1 2 3 4 4\n1 1 2 1 1 2 2\n1 2 2 3 3 4 4\n"
    p = tmp_path / "T010203_0004_001.txt"
    p.write_text(content)
    return p


def test_parse_lee_shin_file_builds_flat_stacks_and_retrieval_queue(small_file):
    state = parse_lee_shin_file(small_file, n_bays=1, n_rows=2, n_tiers=3)
    assert len(state.stacks) == 2
    by_id = {s.id: s for s in state.stacks}
    assert by_id["S1_1"].containers == ["C001", "C002"]  # bottom-to-top, as written
    assert by_id["S1_2"].containers == ["C003", "C004"]
    assert state.retrieval_queue == ["C001", "C002", "C003", "C004"]  # ordered by rank
    assert state.layout.num_stacks == 2
    assert state.layout.max_tier == 3


def test_parse_lee_shin_file_fills_missing_stacks_as_empty(small_file):
    # n_rows=3 but the file only lists rows 1-2 -- row 3 must still exist, empty.
    state = parse_lee_shin_file(small_file, n_bays=1, n_rows=3, n_tiers=3)
    by_id = {s.id: s for s in state.stacks}
    assert by_id["S1_3"].containers == []
    assert len(state.stacks) == 3


def test_parse_lee_shin_file_dedupes_the_repeated_rank_per_container(small_file):
    state = parse_lee_shin_file(small_file, n_bays=1, n_rows=2, n_tiers=3)
    total_containers = sum(len(s.containers) for s in state.stacks)
    assert total_containers == 4  # not 8 -- each rank appears twice in the file, must not be double-counted


@pytest.mark.skipif(not LEE_SHIN_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_find_lee_shin_file_locates_a_real_small_instance():
    path = find_lee_shin_file(inst_type="random", n_bays=2, n_rows=3, n_tiers=6, idx=1)
    assert path.name == "R020306_0020_001.txt"


@pytest.mark.skipif(not LEE_SHIN_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_load_lee_instance_parses_a_real_file_into_a_valid_yard_state():
    state = load_lee_instance(inst_type="random", n_bays=2, n_rows=3, n_tiers=6, idx=1)
    assert state.layout.num_stacks == 6  # 2 bays x 3 rows
    total_containers = sum(len(s.containers) for s in state.stacks)
    assert total_containers == 20
    assert len(state.retrieval_queue) == 20
    assert len(set(state.retrieval_queue)) == 20  # no duplicate container names
