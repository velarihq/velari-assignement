"""Synthetic theses and company generators.

The theses here are deliberately varied: pure conjunctions, disjunctions, and
mixed multi-level trees, with realistic tags and a spread of costs and pass
rates. Use them to develop and benchmark your strategy.

A *company* is represented purely by its criterion outcomes: a dict mapping each
criterion id in a thesis to a bool. ``sample_company`` draws each outcome
independently from the criterion's ``p_pass``. (Real companies have correlated
attributes; modelling that correlation is a listed bonus.)
"""

from __future__ import annotations

import random

from .model import And, Criterion, Node, Or, Thesis, leaves


def _c(cid: str, description: str, tag: str, cost: float, p_pass: float) -> Criterion:
    """Terse constructor for a criterion, to keep the fixtures readable."""
    return Criterion(id=cid, description=description, tag=tag, cost=cost, p_pass=p_pass)


# A pure conjunction. Every criterion must hold. The optimal *static* order is a
# clean, provable result - a good place to start.
CAPITAL_EFFICIENT_SAAS = Thesis(
    name="Capital-efficient EU B2B SaaS",
    root=And(
        (
            _c("profitable", "Is the company profitable or near break-even?", "financials", 8.0, 0.20),
            _c("technical_team", "Is the founding team technical?", "team", 5.0, 0.60),
            _c("eu_hq", "Is the HQ in the EU?", "geography", 2.0, 0.40),
            _c("b2b", "Does it sell primarily to businesses?", "business_model", 1.0, 0.55),
            _c("saas", "Is the product delivered as SaaS?", "business_model", 1.0, 0.35),
        )
    ),
)

# A conjunction gated by a disjunction: the marketplace must hold, plus at least
# one of three growth signals of very different cost and likelihood.
GROWTH_SIGNAL_MARKETPLACE = Thesis(
    name="Marketplace with any strong growth signal",
    root=And(
        (
            _c("marketplace", "Is it a marketplace business?", "business_model", 1.0, 0.30),
            Or(
                (
                    _c("hypergrowth", "Is YoY growth above 100%?", "traction", 4.0, 0.25),
                    _c("marquee_logos", "Does it have marquee enterprise customers?", "traction", 3.0, 0.40),
                    _c("rev_5m", "Is revenue above EUR 5M?", "financials", 8.0, 0.30),
                )
            ),
        )
    ),
)

# A deeper, mixed tree: business-model disjunction, a geography gate, and a
# quality block that is itself a disjunction of an AND and a single signal.
AI_NATIVE_QUALITY = Thesis(
    name="AI-native company with a quality signal",
    root=And(
        (
            Or(
                (
                    _c("ai_native", "Is AI core to the product (not bolted on)?", "product", 3.0, 0.30),
                    _c("vertical_saas", "Is it vertical SaaS for a specific industry?", "business_model", 1.0, 0.35),
                )
            ),
            _c("us_or_eu", "Is HQ in the US or EU?", "geography", 2.0, 0.65),
            Or(
                (
                    And(
                        (
                            _c("profitable_q", "Is it profitable?", "financials", 8.0, 0.20),
                            _c("repeat_founder", "Is there a repeat founder?", "team", 5.0, 0.30),
                        )
                    ),
                    _c("series_a", "Has it raised a priced Series A?", "traction", 4.0, 0.45),
                )
            ),
        )
    ),
)

# A wide flat conjunction of cheap business-model filters plus a couple of
# expensive research criteria - early-exit ordering matters most at scale here.
WIDE_FILTER = Thesis(
    name="Wide cheap-filter thesis",
    root=And(
        (
            _c("software", "Is it primarily a software company?", "business_model", 1.0, 0.60),
            _c("b2b_only", "Is it B2B only (no consumer)?", "business_model", 1.0, 0.50),
            _c("subscription", "Is revenue subscription-based?", "business_model", 1.0, 0.45),
            _c("not_agency", "Is it a product (not an agency/services) business?", "business_model", 1.0, 0.55),
            _c("english_market", "Does it sell into English-speaking markets?", "market", 1.5, 0.70),
            _c("headcount_20_200", "Is headcount between 20 and 200?", "team", 2.0, 0.40),
            _c("rev_2m", "Is revenue above EUR 2M?", "financials", 8.0, 0.35),
            _c("founder_led", "Is it still founder-led?", "team", 5.0, 0.55),
        )
    ),
)

ALL_THESES: tuple[Thesis, ...] = (
    CAPITAL_EFFICIENT_SAAS,
    GROWTH_SIGNAL_MARKETPLACE,
    AI_NATIVE_QUALITY,
    WIDE_FILTER,
)


def sample_company(node: Node, rng: random.Random) -> dict[str, bool]:
    """Draw one company's criterion outcomes for the given thesis subtree.

    Each criterion outcome is an independent Bernoulli draw from its ``p_pass``.

    Args:
        node: The thesis (or subtree) to sample outcomes for.
        rng: Seeded RNG, for reproducibility.

    Returns:
        A dict from criterion id to a boolean outcome.
    """
    return {c.id: rng.random() < c.p_pass for c in leaves(node)}


def sample_companies(thesis: Thesis, n: int, seed: int = 0) -> list[dict[str, bool]]:
    """Draw ``n`` reproducible companies for a thesis.

    Args:
        thesis: The thesis to sample companies for.
        n: Number of companies to draw.
        seed: RNG seed.

    Returns:
        A list of ``n`` outcome dicts.
    """
    rng = random.Random(seed)
    return [sample_company(thesis.root, rng) for _ in range(n)]
