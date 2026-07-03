# Take-home: cost-optimal evaluation of an investment thesis

Welcome, and thanks for taking the time. This exercise is drawn from a real
problem in our product. It is deliberately open-ended: **we care more about how
you think about the problem than about how many lines you write.** A strong
submission can be a few hundred lines plus a clear write-up.

Budget roughly **2-3 focused hours**. If you find yourself going deeper because it's fun, great — but tell us where you stopped and what you'd do next rather than grinding to exhaustion.

---

## 1. Background: what we do

We build an AI platform for investment deal sourcing. An investor defines a
structured **investment thesis** — what kind of company they want to back — and
we evaluate thousands of companies against it, attaching evidence and reasoning
to every decision.

Concretely, a thesis is a **boolean tree of criteria**:

- A **criterion** is one testable question about a company, e.g. *"Is this a B2B
SaaS business?"*, *"Is the HQ in the EU?"*, *"Is the company profitable?"*.
Each criterion carries a **tag** (its category: `business_model`, `geography`,
`financials`, `team`, `market`, `product`, `traction`).
- Criteria are combined with **AND** and **OR** nodes into a tree. A company
**matches** the thesis when the tree evaluates to `True`.

Example thesis — *"Capital-efficient EU B2B SaaS"*:

```
AND
├── profitable        (financials)
├── technical team    (team)
├── HQ in EU          (geography)
├── sells B2B         (business_model)
└── delivered as SaaS (business_model)
```

Here every criterion must hold. Another thesis might be *"a marketplace with **any**
strong growth signal"*:

```
AND
├── marketplace                 (business_model)
└── OR
    ├── >100% YoY growth         (traction)
    ├── marquee customers        (traction)
    └── revenue > EUR 5M         (financials)
```



### The catch: evaluating a criterion is expensive

In production, checking a single criterion means an LLM call or an external data
lookup — real money and real latency. Different criteria cost very different
amounts (a quick "is this SaaS?" is cheap; "is it profitable?" needs digging).

So we never want to evaluate more criteria than necessary. Two levers:

1. **Early exit.** An `AND` is decided the moment one child is `False`; an `OR`
  the moment one child is `True`. Once the *root's* value is pinned down, we
   stop — the remaining criteria don't matter for this company.
2. **Order.** Because of early exit, *the order in which we evaluate criteria
  changes how much we pay.* Checking a cheap, likely-to-fail criterion first
   can settle an `AND` for a fraction of the cost of starting with an expensive
   one.

Each criterion also comes with a prior `p_pass`: the probability that a
random candidate company satisfies it. (In reality we estimate these; here they
are given to you — with a caveat, see the tracks below.)

**That is the whole problem: given a thesis tree, decide what to evaluate and in
what order, per company, to determine the match verdict while paying as little
as possible.**

---



## 2. Your task

You will implement a **strategy**: a policy that, for one company at a time,
repeatedly decides *which criterion to evaluate next*, given what it has learned
so far about that company. The harness stops you the instant the verdict is
determined and charges you for exactly what you evaluated.

We ask you to work through **two tracks**. Do Track 1 well before starting
Track 2; a great Track 1 beats a rushed attempt at both.

### Track 1 — Static ordering (you know the priors)

You may read `cost` **and** `p_pass` for every criterion. Design a strategy that
minimises the **expected cost** of reaching the verdict, exploiting early exit
and the tree structure.

We want to see you reason about *what "optimal" even means* here and how close
you can get. Some questions worth answering in your write-up:

- For a **single** `AND` block of independent criteria, is there a simple rule
that orders them optimally? Can you argue *why* it's optimal?
- Does that rule still hold inside a **nested** tree (AND of ORs of ANDs…)? If
not, what breaks, and what do you do about it?
- What is the *offline optimum* — the fewest-cost evaluations a clairvoyant who
already knew every outcome would need? Can an online strategy match it? If
not, how far off can it be, and why?

Implement the best strategy you can, and **measure** it against the provided
baseline on the fixture theses.

### Track 2 — Online (you must learn the priors)

Now assume `p_pass` is **unknown** (pretend the field isn't there — you may only
use `cost` and the tree). You see a stream of companies one after another. Learn
what you need from the outcomes you observe, and converge toward the Track-1
quality as you see more companies.

Use the `observe(...)` hook to update your estimates between companies. Think
about:

- What guarantee can you make as the stream grows? (Regret vs. the static
optimum, asymptotic optimality, a competitive bound — your call, but be
precise about what you're claiming.)
- There is a subtlety in **what you get to observe**. Look closely at what
`observe` receives after an early exit, and whether naively counting outcomes
gives you an unbiased estimate of `p_pass`. If it doesn't, what would you do?



### Bonus (only if you have time — call out what you'd do, code optional)

- Real company attributes are **correlated** (a profitable company is more
likely to have revenue). How would your approach change if criteria weren't
independent?
- We often evaluate criteria in **parallel batches** (fire *k* LLM calls at
once) to cut latency. How does batching interact with early exit, and how
would you choose batch composition?
- `NOT` nodes / arbitrary monotone formulas; criteria shared across subtrees.

---



## 3. What we give you

```
thesis_ordering/
  model.py       # Criterion, And, Or, Thesis; evaluate_partial (early-exit logic)
  strategy.py    # Strategy base class + relevant_unknown() helper + naive baseline
  evaluator.py   # run_thesis(): the harness that drives a strategy and charges cost
  fixtures.py    # sample theses + reproducible company generators
  benchmark.py   # runs baseline vs your strategy across all theses, prints a table
  candidate.py   # >>> YOUR WORK GOES HERE <<<
tests/
  test_evaluator.py   # sanity tests for the provided harness
```

- `evaluate_partial(node, known)` returns `True`/`False` if the (sub)tree is
already decided by the known outcomes, else `None`. This is the early-exit
logic — read it first.
- `relevant_unknown(root, known)` gives you the criteria still worth
evaluating (unrevealed *and* able to change the verdict). You should never
evaluate anything outside this set.
- The harness raises if you ask for an already-evaluated or irrelevant-by-id
criterion, so bugs surface loudly.

You implement `CandidateStrategy` in `candidate.py`. Everything else is yours to
read but you shouldn't need to change it (if you do, explain why).

---



## 4. Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                              # sanity-check the harness
python -m thesis_ordering.benchmark # baseline vs your strategy
```

Out of the box `CandidateStrategy` falls back to the naive order, so the
benchmark shows `+0.0%`. Your job is to make that number go up.

---



## 5. Deliverables

1. **Code** — your strategy (and any helpers/tests you add). It must run with
  the commands above; the match rate in the benchmark must stay identical to
   the baseline (a strategy that changes verdicts is simply wrong).
2. `DESIGN.md` (~1-2 pages) — the important part. Cover:
  - Your approach for each track and *why*.
  - Your answer to "what does optimal mean here" and how close you get.
  - Any optimality / regret / competitive argument you can make, at whatever
  level of rigour you can support (a precise informal argument beats
  hand-waving; a proof sketch is welcome, not required).
  - Assumptions you made and what you'd do with more time.
  - Your benchmark numbers.

Keep it honest: tell us what you're unsure about. "I think this is optimal for
single blocks but I couldn't prove the nested case, here's my intuition" is a
great sentence to write.

---



## 6. Rules & notes

- **AI tools are allowed.** We use them daily. But you'll be asked to walk us
through and defend *every* decision in a follow-up conversation, so only ship
what you actually understand. We can tell.
- Ask questions if anything is ambiguous — knowing what to clarify is part of
the signal.

Have fun with it. This is a genuinely interesting little problem, and it's very
close to what you'd work on here.