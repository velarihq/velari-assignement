"""Domain model for the thesis-ordering assignment.

An investment *thesis* encodes what a specific investor is looking for. It is a
boolean tree built from three node types:

- ``Criterion`` - a leaf: a single testable question about a company
  (e.g. "Is this a B2B SaaS business?", "Is HQ in the EU?").
- ``And`` - true iff *all* children are true.
- ``Or``  - true iff *at least one* child is true.

A company *matches* a thesis when the tree evaluates to True for that company.

Evaluating a single criterion is expensive: in production each one is an LLM
call or an external data lookup that costs money and latency. The whole point of
this assignment is to determine the tree's value while paying for as *few*
criteria as possible, by exploiting early exit:

- an ``And`` is decided as soon as one child is known False,
- an ``Or``  is decided as soon as one child is known True.

Theses are immutable once created (mirroring the real product), so the node
types are frozen dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Criterion:
    """A single testable condition about a company

    Attributes:
        id: Stable unique identifier used to record outcomes.
        description: Human-readable question the criterion answers.
        tag: Category of the criterion (see ``TAGS``). Business-model criteria
            are cheap signals often used to pre-filter; research criteria tend
            to be more expensive.
        cost: Relative cost of evaluating this criterion (LLM/data spend). The
            unit is arbitrary but consistent across criteria.
        p_pass: Prior probability that a random candidate company satisfies this
            criterion. Used to *generate* synthetic companies and by model-based
            (offline) strategies. See the README for when you may and may not
            read this field.
    """

    id: str
    description: str
    tag: str
    cost: float = 1.0
    p_pass: float = 0.5


@dataclass(frozen=True)
class And:
    """Boolean AND node: true iff every child is true"""

    children: tuple["Node", ...]


@dataclass(frozen=True)
class Or:
    """Boolean OR node: true iff at least one child is true"""

    children: tuple["Node", ...]


Node = Criterion | And | Or


@dataclass(frozen=True)
class Thesis:
    """A named investment thesis: a boolean tree of criteria"""

    name: str
    root: Node


TAGS = (
    "business_model",
    "geography",
    "financials",
    "team",
    "market",
    "product",
    "traction",
)


def leaves(node: Node) -> list[Criterion]:
    """Return every criterion in ``node`` in left-to-right DFS order.

    Args:
        node: The (sub)tree to walk.

    Returns:
        The criteria under ``node``, in declaration order.
    """
    if isinstance(node, Criterion):
        return [node]
    result: list[Criterion] = []
    for child in node.children:
        result.extend(leaves(child))
    return result


def criteria_by_id(thesis: Thesis) -> dict[str, Criterion]:
    """Map every criterion id in ``thesis`` to its ``Criterion``.

    Args:
        thesis: The thesis whose criteria to index.

    Returns:
        A dict from criterion id to criterion.
    """
    return {c.id: c for c in leaves(thesis.root)}


def evaluate_partial(node: Node, known: dict[str, bool]) -> bool | None:
    """Evaluate ``node`` under a partial assignment of criterion outcomes.

    Args:
        node: The (sub)tree to evaluate.
        known: Outcomes revealed so far, keyed by criterion id.

    Returns:
        ``True`` or ``False`` if the value is already determined by ``known``
        regardless of the unrevealed criteria, otherwise ``None``.
    """
    if isinstance(node, Criterion):
        return known.get(node.id)

    child_values = [evaluate_partial(c, known) for c in node.children]

    if isinstance(node, And):
        if any(v is False for v in child_values):
            return False
        if all(v is True for v in child_values):
            return True
        return None

    if any(v is True for v in child_values):
        return True
    if all(v is False for v in child_values):
        return False
    return None
