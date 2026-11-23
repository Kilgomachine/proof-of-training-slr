# AI assistance

A large language model (Claude, Anthropic) was used as a second reader and as a coding assistant. This file records, stage by stage, what the model did, what the author did, and where each result is in this package. The paper's Section 3.6 describes the same process.

| Stage | What the model did | What the author did | Files |
|---|---|---|---|
| Title and abstract screening, database search (656) | Screened every record against the written rubric, without access to the author's decisions | Screened every record; the author's decision is the one used | `database_screening_author.csv`, `database_screening_automated.csv` |
| Screening of snowballing candidates (2,649 + 637) | Screened every candidate against the written rubric | Screened every candidate without seeing the automated decision; the author's decision is the one used | `backward_screening.csv`, `forward_screening.csv` (`author_*` and `automated_*` columns) |
| Three screening questions (1,293) | Coded Q1 to Q3 (40 calibration records one by one, the rest in batches), then re-checked the coding: a blind second review of the decision-relevant rows and a full-text reading of the rows where the two reviews disagreed | Answered Q1 to Q3 for the same records | `three_questions_automated.csv`, `three_questions_recheck_log.csv`, `three_questions_author.csv` |
| Classification of the full texts (type, in or out) | Read every full text twice, the second pass blind to the first, and proposed a type and a status with page references | Classified the studies independently by colour coding in the selection spreadsheet (118 of the 125 included studies carry the author's colour), settled disagreements by the written rulings, and made every inclusion decision | `full_text_assessment.csv`, `borderline_rechecks.csv`, [rulings.md](rulings.md) |
| Extraction of the cryptographic studies (technique, coverage, who checks, setup, cost, assumptions) | Re-read the 54 full texts and extracted the fields with page references | Decided the nine fields on which the two readings differed | `crypto_extraction.csv` |
| Codings derived from the extraction: sub-types of the non-cryptographic types, scope level, assumption groups, prototype gap, code links, limitations, metrics | Coded every study from the extraction and the full texts | Checks of these codings on samples of ten studies are prepared; see below | `verification_scope.csv`, `crypto_assumptions*.csv`, `crypto_prototype_gap.csv`, `crypto_code_links.csv`, `crypto_limitations_qac5.csv`, `crypto_metrics.csv`, `noncrypto_extraction.csv` |
| Scripts | The snowballing and coverage scripts were written with the model's assistance | Ran the scripts on the Scopus exports | `scripts/` |

## Agreement with the automated pass

Agreement on keep/exclude between the author and the automated screening pass: 96.8% for the database search (Cohen's κ = 0.89), 96.5% for backward candidates (κ = 0.56) and 97.6% for forward candidates (κ = 0.76). These are agreements with an automated pass, not inter-rater reliability. No second human rater screened the records or extracted a sample of the studies.

## Status of the author's checks

The derived codings in the sixth row were produced by the model. Samples of ten studies were drawn for the author to check each set (scope levels and assumptions; non-cryptographic metrics; cryptographic metrics). The results of these checks will be recorded here.
