<!--
  Replace the section headings with your content.
  Delete sections that don't apply (e.g. "Cost impact" if there is none).
  See docs/DEVELOPMENT.md §4 for PR rules; docs/PLAN.md §10 for the DoD.
-->

## What & why

<!-- 1–3 sentences. What changed and why. Skip the play-by-play of file diffs. -->

## Linked issues

Closes #

<!-- Or: Refs #N if not closing -->

## Demo

<!-- Required for any user-facing change. Drag in a screenshot or GIF. -->
<!-- For API/CLI changes, paste the input + output. -->

## Definition of Done (docs/PLAN.md §10)

- [ ] Code merged via PR (no direct pushes to `main`)
- [ ] Unit tests added; coverage ≥ 80% on new code (verified via `make test`)
- [ ] Integration test added if change crosses a service boundary
- [ ] Eval metric recorded in `eval/reports/` if model output changed
- [ ] Docs updated (`docs/` and/or package README) if user-facing
- [ ] Demo GIF / screenshot in this PR description
- [ ] CI green (lint + test + build + eval-smoke)
- [ ] Cost impact noted below if architecture changes

## Cost impact

<!--
  Skip if none.
  Otherwise estimate $/mo delta and which line in docs/DEPLOYMENT.md §10 changes.
  Reminder: $50/mo hard cap.
-->

## Sprint

<!-- e.g. S0 / S1 / hotfix. Used by the project board automation. -->

## Reviewer checklist

- [ ] Diff fits in head; opened "Files changed" tab and added at least one review comment (self-review rule, DEVELOPMENT.md §4)
- [ ] No `TODO: later` in critical path (anti-pattern, DEVELOPMENT.md §12)
- [ ] No new dependency without an issue (DEVELOPMENT.md §7)
- [ ] Secrets / PII not introduced
