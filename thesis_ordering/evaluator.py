"""The evaluation harness.

Given a thesis, a company's true criterion outcomes, and a strategy that decides
what to evaluate next, ``run_thesis`` walks the strategy through the company one
criterion at a time and stops the instant the thesis value is determined. It
records what was evaluated and the total cost paid.

This harness is the ground truth for scoring: your strategy only ever sees a
criterion's outcome by asking for it here, and every ask is charged.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Thesis, criteria_by_id, evaluate_partial
from .strategy import Strategy, relevant_unknown


@dataclass
class Trace:
    """Record of one thesis evaluation for one company

    Attributes:
        verdict: Whether the company matched the thesis.
        evaluated: Criterion ids in the order they were evaluated.
        total_cost: Sum of ``cost`` over evaluated criteria.
    """

    verdict: bool
    evaluated: list[str]
    total_cost: float

    @property
    def n_evaluated(self) -> int:
        """Number of criteria evaluated before the verdict was reached."""
        return len(self.evaluated)


def run_thesis(thesis: Thesis, outcomes: dict[str, bool], strategy: Strategy) -> Trace:
    """Drive ``strategy`` through one company and return the resulting trace.

    Args:
        thesis: The thesis to evaluate.
        outcomes: The company's true outcome for every criterion id.
        strategy: The policy deciding which criterion to evaluate next.

    Returns:
        A ``Trace`` of the evaluation.

    Raises:
        ValueError: If the strategy asks for a criterion that is unknown,
            already evaluated, or no longer relevant to the verdict.
    """
    by_id = criteria_by_id(thesis)
    known: dict[str, bool] = {}
    evaluated: list[str] = []
    total_cost = 0.0

    while True:
        verdict = evaluate_partial(thesis.root, known)
        if verdict is not None:
            return Trace(verdict, evaluated, total_cost)

        cid = strategy.next_criterion(thesis, known)
        if cid not in by_id:
            raise ValueError(f"strategy asked for unknown criterion {cid!r}")
        if cid in known:
            raise ValueError(f"strategy re-asked criterion {cid!r}")
        if cid not in {c.id for c in relevant_unknown(thesis.root, known)}:
            raise ValueError(f"strategy asked for irrelevant criterion {cid!r}")

        known[cid] = outcomes[cid]
        evaluated.append(cid)
        total_cost += by_id[cid].cost
