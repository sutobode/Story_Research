import random
from dataclasses import dataclass

from scipy import stats as scipy_stats


@dataclass
class WilcoxonResult:
    p_value: float
    n_pairs: int
    n_nonzero_pairs: int


def bootstrap_ci(
    values: list[float], n_resamples: int = 2000, ci: float = 0.95, rng: random.Random | None = None
) -> tuple[float, float, float]:
    """Bootstrap mean +/- CI (spec 23.6). Uses stdlib `random`, not numpy's
    RNG, so results are reproducible with the same seed convention as the
    rest of this codebase."""
    rng = rng or random.Random()
    n = len(values)
    mean = sum(values) / n
    resample_means = []
    for _ in range(n_resamples):
        resample = [values[rng.randrange(n)] for _ in range(n)]
        resample_means.append(sum(resample) / n)
    resample_means.sort()
    lo_idx = int((1 - ci) / 2 * n_resamples)
    hi_idx = int((1 - (1 - ci) / 2) * n_resamples) - 1
    return mean, resample_means[lo_idx], resample_means[hi_idx]


def wilcoxon_signed_rank(a: list[float], b: list[float]) -> WilcoxonResult:
    """Paired Wilcoxon signed-rank test (spec 23.6) -- p-value for whether
    `a` and `b` (same seeds, same instance) differ. Delegates to scipy rather
    than a hand-rolled rank-sum implementation: this exact number is what a
    Q1 reviewer will scrutinize.

    Uses zero_method="pratt": scipy's default ("wilcox") silently drops
    zero-difference pairs from the ranking, which would inflate apparent
    significance if many seeds show no difference. Pratt keeps them in the
    ranking instead, and n_nonzero_pairs is disclosed alongside n_pairs so a
    reviewer (or the report) can see how many seeds actually differed."""
    n_pairs = len(a)
    n_nonzero_pairs = sum(1 for x, y in zip(a, b) if x != y)
    if n_nonzero_pairs == 0:
        return WilcoxonResult(p_value=1.0, n_pairs=n_pairs, n_nonzero_pairs=0)
    _, p_value = scipy_stats.wilcoxon(a, b, zero_method="pratt")
    return WilcoxonResult(p_value=float(p_value), n_pairs=n_pairs, n_nonzero_pairs=n_nonzero_pairs)


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni step-down correction (spec 23.6). Returns, in the
    SAME order as the input, whether each comparison's null hypothesis is
    rejected at the family-wise `alpha`."""
    n = len(p_values)
    order = sorted(range(n), key=lambda i: p_values[i])
    reject = [False] * n
    for rank, idx in enumerate(order):
        threshold = alpha / (n - rank)
        if p_values[idx] <= threshold:
            reject[idx] = True
        else:
            break  # step-down: once one fails, all remaining (larger p) fail too
    return reject


def cliffs_delta(a: list[float], b: list[float]) -> float:
    """Cliff's delta effect size (spec 23.6), in [-1, 1]. Positive means `a`
    values tend to exceed `b` values; 0 means no stochastic dominance either way."""
    greater = sum(1 for x in a for y in b if x > y)
    less = sum(1 for x in a for y in b if x < y)
    return (greater - less) / (len(a) * len(b))
