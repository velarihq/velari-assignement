"""Sanity tests for the harness. Run with ``pytest``.

These verify the provided infrastructure - not your strategy. If they pass, your
environment is set up correctly. Add your own tests for your strategy.
"""

from __future__ import annotations

from thesis_ordering.evaluator import run_thesis
from thesis_ordering.fixtures import ALL_THESES, sample_companies
from thesis_ordering.model import And, Criterion, Or, Thesis, evaluate_partial
from thesis_ordering.strategy import DeclarationOrderStrategy, relevant_unknown


def _full_verdict(thesis: Thesis, outcomes: dict[str, bool]) -> bool:
    """Evaluate the thesis with every outcome known - the ground-truth verdict."""
    value = evaluate_partial(thesis.root, outcomes)
    assert value is not None
    return value


def test_evaluate_partial_and_or() -> None:
    """AND early-exits on the first False; OR early-exits on the first True."""
    a = Criterion("a", "", "t", 1.0, 0.5)
    b = Criterion("b", "", "t", 1.0, 0.5)
    assert evaluate_partial(And((a, b)), {"a": False}) is False
    assert evaluate_partial(And((a, b)), {"a": True}) is None
    assert evaluate_partial(Or((a, b)), {"a": True}) is True
    assert evaluate_partial(Or((a, b)), {"a": False}) is None


def test_baseline_returns_correct_verdict() -> None:
    """The baseline verdict matches full evaluation for every fixture company."""
    for thesis in ALL_THESES:
        for company in sample_companies(thesis, 200, seed=1):
            trace = run_thesis(thesis, company, DeclarationOrderStrategy())
            assert trace.verdict == _full_verdict(thesis, company)


def test_early_exit_saves_evaluations() -> None:
    """Early exit means we usually evaluate fewer than all criteria."""
    thesis = ALL_THESES[0]
    companies = sample_companies(thesis, 500, seed=2)
    total_leaves = len(thesis.root.children)
    evals = [run_thesis(thesis, c, DeclarationOrderStrategy()).n_evaluated for c in companies]
    assert min(evals) < total_leaves


def test_relevant_unknown_excludes_decided_subtrees() -> None:
    """Once a subtree is decided, its criteria are no longer relevant."""
    a = Criterion("a", "", "t", 1.0, 0.5)
    b = Criterion("b", "", "t", 1.0, 0.5)
    c = Criterion("c", "", "t", 1.0, 0.5)
    thesis = Thesis("t", And((Or((a, b)), c)))
    relevant = {crit.id for crit in relevant_unknown(thesis.root, {"a": True})}
    assert relevant == {"c"}
