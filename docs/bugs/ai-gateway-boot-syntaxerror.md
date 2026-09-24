# Bug: AI gateway couldn't import — one-line SyntaxError

**Severity:** Fatal (whole service dead) · **Status:** FIXED 2026-09-24 · **Found:** 2026-09-24

## Symptom
Nothing in the Python AI gateway would boot. `python -c "import app.main"` failed immediately.

## How I found it
Tried to import the app and read the traceback — a `SyntaxError` pointing into `app/agents/base_executor.py`.

## Root cause
`base_executor.py:253` had two statements collapsed onto one physical line — a stray edit had eaten the newline:
```python
state.delegation_message = message            logger.info("agent_delegation", ...)
```
Because `base_executor` is imported transitively by `app.main`, this single line broke the **entire** import graph above it — every agent, every route.

## Blast radius
100% of ai-gateway functionality dead. This is the real reason "the agents are dumb": they never ran at all.

## Fix
Split the two statements back onto separate lines:
```python
state.delegation_message = message
logger.info("agent_delegation", from_agent=self.name, to_agent=target_role, trace_id=get_trace_id())
```
Then I AST-parsed all 91 `app/**.py` files to confirm no other syntax errors were hiding — all clean.

## Tradeoff
None on the fix itself. The lesson is about prevention.

## Interview lesson
A syntax error in a hot-path module is a **fail-closed dependency** — one bad line deep in the import graph blocks everything above it. A pre-commit `python -m py_compile` / ruff step in CI catches this before merge. It's my go-to argument for cheap static gates in the pipeline.
