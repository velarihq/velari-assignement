"""Strategy interface and the naive baseline.

A *strategy* decides, given the thesis and the outcomes revealed so far for the
current company, which criterion to evaluate next. It may also learn across
companies via ``observe``.

Implement your own strategy by subclassing ``Strategy``. The whole assignment is
about making ``next_criterion`` smart.
"""

from __future__ import annotations

from .model import Criterion, Node, Thesis, evaluate_partial


class Strategy:
    """Base strategy - subclass and override ``next_criterion``"""

    def next_criterion(self, thesis: Thesis, known: dict[str, bool]) -> str:
        """Return the id of the next criterion to evaluate.

        Args:
            thesis: The thesis being evaluated.
            known: Per-company working state mapping criterion id -> bool. Starts
                empty and grows by one entry each time you return a criterion (the
                harness fills in its outcome); it is reset to empty for every new
                company. Only criteria you have already asked for appear here.

                What you may read off each ``Criterion`` to decide depends on the
                track: Track 1 may use ``cost`` and ``p_pass``; Track 2 may use
                ``cost`` and the tree only, treating ``p_pass`` as absent and
                relying on estimates learned in ``observe``.

        Returns:
            The id of an unrevealed criterion whose value can still influence
            the thesis verdict.
        """
        raise NotImplementedError

    def observe(self, outcomes: dict[str, bool]) -> None:
        """Accumulate cross-company knowledge from a finished evaluation.

        Called once per company, after its verdict. Since ``known`` is wiped
        between companies, this is your only channel for memory that persists
        across the stream: fold anything you want to learn (e.g. estimated pass
        rates) into ``self`` here. The Track-2 learning hook - the default no-op
        suffices for Track 1, which reads ``p_pass`` directly.

        Args:
            outcomes: Outcomes of the company just evaluated, mapping criterion
                id -> bool. Keys are only the criteria evaluated before that
                company's verdict (``trace.evaluated``), not all of them. Mind
                the sampling bias flagged in the README: because early exit
                decides *which* criteria you see, naively counting True/False is
                a biased estimator of the true ``p_pass``.
        """


def relevant_unknown(node: Node, known: dict[str, bool]) -> list[Criterion]:
    """Return criteria that are unrevealed and can still move the verdict.

    A criterion is *relevant* if revealing it could change whether the tree is
    determined - i.e. it sits under a subtree that is not yet decided. Wasting
    an evaluation on an irrelevant criterion is never optimal.

    Args:
        node: The (sub)tree to inspect.
        known: Outcomes revealed so far for the current company.

    Returns:
        The relevant unrevealed criteria, in declaration order.
    """
    if evaluate_partial(node, known) is not None:
        return []
    if isinstance(node, Criterion):
        return [] if node.id in known else [node]
    result: list[Criterion] = []
    for child in node.children:
        result.extend(relevant_unknown(child, known))
    return result


class DeclarationOrderStrategy(Strategy):
    """Naive baseline: evaluate relevant criteria in tree (DFS) order

    Correct but not cost-aware. This is the bar to beat.
    """

    def next_criterion(self, thesis: Thesis, known: dict[str, bool]) -> str:
        """Return the first relevant unknown criterion in DFS order."""
        return relevant_unknown(thesis.root, known)[0].id
