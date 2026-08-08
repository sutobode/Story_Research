import random
from sarcrp.stats import bootstrap_ci, wilcoxon_signed_rank, holm_bonferroni, cliffs_delta


def test_bootstrap_ci_bounds_contain_the_mean():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, lo, hi = bootstrap_ci(values, n_resamples=500, ci=0.95, rng=random.Random(0))
    assert lo <= mean <= hi


def test_bootstrap_ci_is_seed_reproducible():
    values = [1.0, 5.0, 2.0, 8.0, 3.0]
    a = bootstrap_ci(values, n_resamples=200, rng=random.Random(7))
    b = bootstrap_ci(values, n_resamples=200, rng=random.Random(7))
    assert a == b


def test_wilcoxon_signed_rank_identical_samples_gives_high_p_value():
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = wilcoxon_signed_rank(a, list(a))
    assert result.p_value == 1.0  # all paired differences are zero
    assert result.n_pairs == 5
    assert result.n_nonzero_pairs == 0


def test_wilcoxon_signed_rank_detects_a_consistent_shift():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    b = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]  # every pair b > a by exactly 1
    result = wilcoxon_signed_rank(a, b)
    assert result.p_value < 0.05
    assert result.n_pairs == 8
    assert result.n_nonzero_pairs == 8


def test_wilcoxon_signed_rank_discloses_partial_zero_pairs_using_pratt():
    # scipy's default zero_method="wilcox" silently drops zero-difference
    # pairs; this codebase requires "pratt" (keeps them in the ranking) and
    # requires disclosing how many pairs were actually non-zero, per the
    # user's fairness/rigor requirement -- a reviewer must be able to see
    # that 2 of 5 seeds showed no difference at all, not just a p-value.
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [1.0, 2.0, 5.0, 6.0, 7.0]  # first two pairs tie, last three differ
    result = wilcoxon_signed_rank(a, b)
    assert result.n_pairs == 5
    assert result.n_nonzero_pairs == 3
    assert 0.0 <= result.p_value <= 1.0


def test_holm_bonferroni_rejects_fewer_than_uncorrected():
    p_values = [0.01, 0.04, 0.03, 0.20, 0.005]
    corrected = holm_bonferroni(p_values, alpha=0.05)
    uncorrected = [p < 0.05 for p in p_values]
    assert sum(corrected) <= sum(uncorrected)
    assert len(corrected) == len(p_values)


def test_cliffs_delta_no_overlap_gives_extreme_value():
    a = [1.0, 2.0, 3.0]
    b = [10.0, 11.0, 12.0]
    delta = cliffs_delta(a, b)
    assert delta == -1.0  # every a < every b


def test_cliffs_delta_identical_distributions_gives_zero():
    a = [1.0, 2.0, 3.0]
    assert cliffs_delta(a, list(a)) == 0.0
