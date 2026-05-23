# Golden eval set

Versioned Tanglish→Tamil pairs used by `eval/run.py`. Treat as code: every change goes through a PR, never edited live.

## Versions

| File     | Pairs                 | Status | Notes                                                                                                                                          |
| -------- | --------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `v1.csv` | **70** (initial seed) | DRAFT  | Machine-drafted by `sc-draft`. Target: 1000 pairs (S0-4 acceptance). Needs human review by Tamil-school volunteers before declaring S0-4 done. |

## Composition (target 1000 pairs)

Per `docs/TESTING.md` §4.1:

| Domain         | Target   | Current v1 | Description                                                          |
| -------------- | -------- | ---------- | -------------------------------------------------------------------- |
| `conversation` | 200      | 20         | Greetings, family, household, common questions                       |
| `names`        | 200      | 20         | People (Tamil + diaspora), cities, brands, films, historical figures |
| `school`       | 200      | 10         | Math, science, classroom interactions, homework                      |
| `news`         | 200      | 10         | Headlines, government, weather, economy (formal register)            |
| `code_switch`  | 200      | 10         | English nouns/verbs preserved verbatim with Tamil grammar            |
| **TOTAL**      | **1000** | **70**     |                                                                      |

## Schema (columns)

| Column           | Type   | Required | Notes                                                        |
| ---------------- | ------ | -------- | ------------------------------------------------------------ |
| `id`             | string | yes      | Format: `<domain-prefix>-<NNN>` (e.g. `conv-042`)            |
| `tanglish`       | string | yes      | Input — Tamil written in Roman script                        |
| `expected_tamil` | string | yes      | Tamil Unicode target                                         |
| `domain`         | enum   | yes      | `conversation` / `names` / `school` / `news` / `code_switch` |
| `difficulty`     | enum   | yes      | `easy` / `medium` / `hard`                                   |
| `reviewer`       | string | yes      | Initials of native-speaker reviewer who verified             |
| `notes`          | string | no       | Free text — register, dialect, ambiguity flag                |

## Reviewer status

| Initials    | Name                        | Role                               | Pairs reviewed |
| ----------- | --------------------------- | ---------------------------------- | -------------- |
| `sc-draft`  | (machine-drafted by Claude) | bootstrap only — NOT a real review | 70 / 70        |
| _(pending)_ | Tamil-school volunteer      | native-speaker review              | 0              |
| _(pending)_ | Second native reviewer      | inter-rater agreement              | 0              |

**Until at least one human reviewer signs off, treat metrics from this set as directional only.**

## Review workflow (S0-4 unblock)

For each pair:

1. **Tanglish input** — is it natural? (would a kid actually type this?)
2. **Tamil target** — is the script correct? Spelling? Sandhi joins?
3. **Domain tag** — does it fit the labeled domain?
4. **Difficulty** — does it match? (easy = single common word; medium = phrase; hard = full sentence / code-switch / formal register)
5. **Initials in `reviewer` column** — replaces `sc-draft`
6. **Notes** — flag ambiguity, alternate valid spellings, dialect variation

If a pair is wrong, fix the `expected_tamil`. If unsalvageable, delete the row and add a replacement with a new `id`.

## Adding pairs

- Always increment `id` within the domain prefix; never re-use a deleted id (so eval reports are reproducible).
- Hand-curated > scraped > machine-drafted, in that order.
- For code-switched pairs, prefer **real** English words kids type (call, message, homework, video, link) over contrived combinations.
- Avoid PII (real student names, addresses, school identifiers).

## Outreach template for volunteer reviewers

> Hi [name],
>
> We're building a free open-source tool to help Tamil-learning kids type Tamil (Tanglish → Tamil). We need native Tamil speakers to review a benchmark dataset of ~1000 phrase pairs. Each pair takes ~30 sec to verify. The full set takes about 5–8 hours total, splittable across sessions.
>
> Volunteers are credited by initials in the repo, listed in the AOST research paper acknowledgments, and get early access to the tool.
>
> Repo: https://github.com/chandralabs/tamil-edu-toolkit/blob/main/data/golden/v1.csv
> Review guide: https://github.com/chandralabs/tamil-edu-toolkit/blob/main/data/golden/README.md
>
> Interested?
>
> — chandralabs (Academy of Smart Thinkers)
