"""Benchmark harness: run strategies across the fixture theses and report cost.

Run it with:

    python -m thesis_ordering.benchmark

It prints, per thesis, the average cost and average number of criteria evaluated
for the naive baseline and for your ``CandidateStrategy``, plus the match rate
(which must be identical - a strategy that changes verdicts is wrong).
"""

from __future__ import annotations

from collections.abc import Callable
from statistics import mean

from .candidate import CandidateStrategy
from .evaluator import run_thesis
from .fixtures import ALL_THESES, sample_companies
from .model import Thesis
from .strategy import DeclarationOrderStrategy, Strategy

N_COMPANIES = 5000
SEED = 7


def evaluate_strategy(
    factory: Callable[[], Strategy],
    thesis: Thesis,
    n: int = N_COMPANIES,
    seed: int = SEED,
) -> tuple[float, float, float]:
    """Run a fresh strategy instance over ``n`` companies for one thesis.

    Args:
        factory: Zero-arg callable returning a fresh strategy (state resets per
            thesis, but persists across companies within the thesis).
        thesis: The thesis to evaluate.
        n: Number of companies.
        seed: RNG seed.

    Returns:
        A tuple of (mean cost, mean criteria evaluated, match rate).
    """
    companies = sample_companies(thesis, n, seed)
    strategy = factory()
    costs: list[float] = []
    counts: list[int] = []
    matched = 0

    for company in companies:
        trace = run_thesis(thesis, company, strategy)
        strategy.observe({cid: company[cid] for cid in trace.evaluated})
        costs.append(trace.total_cost)
        counts.append(trace.n_evaluated)
        matched += int(trace.verdict)

    return mean(costs), mean(counts), matched / n


def main() -> None:
    """Print a comparison table of baseline vs candidate across all theses."""
    header = f"{'thesis':<40}{'strategy':<14}{'avg_cost':>10}{'avg_evals':>11}{'match_rate':>12}"
    print(header)
    print("-" * len(header))

    for thesis in ALL_THESES:
        base_cost, base_evals, base_match = evaluate_strategy(DeclarationOrderStrategy, thesis)
        cand_cost, cand_evals, cand_match = evaluate_strategy(CandidateStrategy, thesis)

        print(f"{thesis.name:<40}{'baseline':<14}{base_cost:>10.3f}{base_evals:>11.3f}{base_match:>12.3f}")
        savings = 100.0 * (1.0 - cand_cost / base_cost) if base_cost else 0.0
        print(
            f"{'':<40}{'candidate':<14}{cand_cost:>10.3f}{cand_evals:>11.3f}{cand_match:>12.3f}"
            f"   ({savings:+.1f}% cost vs baseline)"
        )
        print()


if __name__ == "__main__":
    main()
