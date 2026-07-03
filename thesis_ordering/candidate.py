"""Your work goes here.

Replace the body of ``CandidateStrategy`` with a cost-aware policy that exploits
early exit and the tree structure. Out of the box it just falls back to the
naive declaration order so the benchmark runs - beating that is the assignment.

You are free to add fields, helpers, and precomputation. If you build an online
strategy that estimates pass rates, use ``observe``. See the README for the two
tracks and the rules on when you may read ``criterion.p_pass``.
"""

from __future__ import annotations

from .model import Thesis
from .strategy import Strategy, relevant_unknown


class CandidateStrategy(Strategy):
    """Cost-aware ordering strategy - implement me"""

    def next_criterion(self, thesis: Thesis, known: dict[str, bool]) -> str:
        """Return the next criterion to evaluate.

        Args:
            thesis: The thesis being evaluated.
            known: Outcomes revealed so far for the current company.

        Returns:
            The id of the criterion to evaluate next.
        """
        # TODO: replace this naive fallback with your ordering logic.
        return relevant_unknown(thesis.root, known)[0].id
