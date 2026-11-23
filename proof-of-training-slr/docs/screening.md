# Screening and snowballing

## Decisions

Every record has one decision and, if excluded, one criterion code (the lowest-numbered criterion that applies; see [protocol.md](protocol.md)). Decisions take four values:

| Decision | Meaning |
|---|---|
| `include` | Meets the criteria on the title and abstract |
| `include-borderline` | Cannot be judged from the abstract; carried to full text (kept) |
| `exclude-borderline` | Probably out; excluded, flagged as a close call |
| `exclude` | Clearly out |

`include` and `include-borderline` count as kept. The author's spreadsheet recorded decisions and codes by hand, with spelling variants (`Eclude`, `EC 5`, ...); the files keep the value as recorded next to the normalised one (`decision_as_recorded`, `criterion_as_recorded`). A code recorded as `TEE` marks a trusted-hardware record kept as borderline because its root of trust could not be judged from the abstract.

## Database search (656 records)

- File: [`data/2_screening/database_screening_author.csv`](../data/2_screening/database_screening_author.csv).
- Result: 114 kept (98 `include`, 16 `include-borderline`), 542 excluded.
- The same 656 records were also screened by an automated pass that applied the written rubric ([screening-rubric.md](screening-rubric.md)) without access to the author's decisions. The paper reports agreement on keep/exclude of 96.8% (Cohen's κ = 0.89, 655 records compared). The automated decisions for this stage are in `data/2_screening/database_screening_automated.csv`.

## Backward snowballing (2,649 candidates)

Seeds: the 114 records kept from the database search.

| Step | Count |
|---|---|
| References in the seeds' reference lists (Scopus export) | 4,119 |
| Distinct works after matching normalised titles (lower case, punctuation removed) | 3,285 |
| Near-duplicate titles merged (Python `difflib` ratio ≥ 0.95 over the length of the shorter title) | −594 |
| Works already screened in the database search | −42 |
| **Candidates screened** | **2,649** |
| Kept | 66 |

- File: [`data/2_screening/backward_screening.csv`](../data/2_screening/backward_screening.csv). Backward candidates carry a title and the reference string's venue only; there is no abstract.
- Script: [`scripts/snowballing/backward_snowball.py`](../scripts/snowballing/backward_snowball.py).

## Forward snowballing (637 candidates)

| Step | Count |
|---|---|
| Citing records exported from Scopus (three seed blocks) | 892 rows |
| Distinct citing papers | 792 |
| Seeds themselves | −66 |
| Already screened in the database search | −41 |
| Already among the backward candidates | −48 |
| **Candidates screened** | **637** |
| Kept | 26 |

[`data/2_screening/forward_removals.csv`](../data/2_screening/forward_removals.csv) lists the 156 citing records flagged for removal before screening (66 seeds matched by EID, 41 already screened, 49 matched to a backward candidate), with the matched title and its similarity. One flagged record was a false match and was kept as candidate F0579, so 155 were removed.

The Scopus export does not say which seed a record cites; the link was recovered from the citing papers' own reference lists for 598 of the 637 candidates (`citation_edge_status`), and the remaining 39 were screened as well.

- File: [`data/2_screening/forward_screening.csv`](../data/2_screening/forward_screening.csv).
- Scripts: [`scripts/snowballing/forward_snowball.py`](../scripts/snowballing/forward_snowball.py), [`scripts/snowballing/verify_forward_coverage.py`](../scripts/snowballing/verify_forward_coverage.py).

One round of each was run. It added 29 included studies (15 forward, 14 backward), so the usual stopping condition (a round that finds nothing new) was not met.

## Agreement with the automated pass

Each snowballing candidate was screened by the author and by an automated, LLM-assisted pass applying the written rubric; the author recorded each decision without seeing the automated one. Both decisions are in the screening files (`author_decision`, `automated_decision`). Counting `include` and `include-borderline` as kept:

| | Backward | Forward |
|---|---|---|
| Both keep | 64 | 25 |
| Author keeps, automated pass excludes | 2 | 1 |
| Author excludes, automated pass keeps | 92 | 14 |
| Both exclude | 2,491 | 597 |
| Agreement | 96.5% | 97.6% |
| Cohen's κ | 0.56 | 0.76 |

These figures are agreement with an automated pass, not inter-rater reliability: no second human rater screened the records. `python scripts/reproduce_numbers.py` recomputes them from the files.

## Three screening questions (cross-check)

Records from the database search and forward snowballing (1,293) were also coded on three questions: Q1, is the paper about training a machine learning model? Q2, is the training distributed across several parties? Q3, does the paper produce evidence a second party can verify? Answers are `Y`, `N` or `U` (unclear). Q1 and Q3 restate IC-2 and IC-3; Q2 records the setting and does not exclude.

- [`three_questions_automated.csv`](../data/2_screening/three_questions_automated.csv): the automated coding (`coded` = `hand` for the 40 calibration records coded one by one before the batches, `batch` for the rest), with flags such as `AGGREGATION-ONLY` or `BYZANTINE-ONLY`.
- [`three_questions_recheck_log.csv`](../data/2_screening/three_questions_recheck_log.csv): the answers changed when the automated coding was re-checked, with the reason for each.
- [`three_questions_author.csv`](../data/2_screening/three_questions_author.csv): the author's own answers.

## Full text

- [`data/3_full_text/full_text_assessment.csv`](../data/3_full_text/full_text_assessment.csv): the 206 records kept by the three sources, plus P132 (excluded at database screening, read for information), with the status after full-text reading.
- [`data/3_full_text/full_texts_not_available.csv`](../data/3_full_text/full_texts_not_available.csv): records whose full text could not be obtained or that could not be found.
- [`data/3_full_text/borderline_rechecks.csv`](../data/3_full_text/borderline_rechecks.csv): how each classification first marked as unsure was re-checked.

| Stage | Count |
|---|---|
| Kept by the three sources (114 + 66 + 26) | 206 |
| Backward candidates repeating a database record | −19 |
| Unique studies | 187 |
| Not assessable: no full text (14), reference not found (7), not a paper (2) | −23 |
| Assessed in full | 164 |
| Excluded: does not verify training (33), preprint without peer review (IC-1, 3), thesis (EC-4, 2), repeat of a record excluded at database screening (1) | −39 |
| **Included** | **125** (96 database, 15 forward, 14 backward) |

For the 33 full-text exclusions, the spreadsheet records the reason in words; the criterion code in the file is derived from that reason (`criterion_source` = `derived`): EC-5 for 31, EC-6 for B1740 (traces others' use of marked data) and EC-2 for B1903 (simulation outputs, not machine learning training).
