# Data dictionary

All files are UTF-8 CSV with a header row. IDs: `P001`–`P656` database records, `B0001`–`B2649` backward candidates, `F0001`–`F0637` forward candidates; the paper cites studies by these IDs. Values are recorded as the studies state them; an empty cell means not recorded or not reported. Codes are explained in [codebook.md](codebook.md).

## 1_search

**`database_records.csv`** — the 656 records of the frozen Scopus search (bibliographic fields only).
`id`, `eid` (Scopus EID), `doi`, `title`, `authors`, `year`, `source_title`, `volume`, `issue`, `article_no`, `pages`, `document_type`, `duplicate_count` (records sharing the normalised title), `duplicate_of`.

**`validation_set.csv`** — the six studies the query had to keep returning. `id`, `eid`, `doi`, `title`, `venue`, `year`.

**`scopus_query.txt`** — the search string. **`forward_snowballing_seed_blocks.txt`** — the three EID blocks used for the cited-by search.

## 2_screening

**`database_screening_author.csv`** — the author's title and abstract decision for each of the 656 records.
`id`, `eid`, `title`, `decision` (normalised: include, include-borderline, exclude-borderline, exclude), `criterion` (normalised code, screening numbering; see [protocol.md](protocol.md#criteria-numbering-at-screening)), `decision_as_recorded`, `criterion_as_recorded`, `note`.

**`database_screening_automated.csv`** — the automated pass's decision for each of the 656 records.
`id`, `decision` and `criterion` (same values and numbering as the author's file), `note` (the pass's one-line reason), `confidence` (high, medium, low).

**`backward_screening.csv`** — the 2,649 backward candidates.
`sbid`, `title`, `authors`, `year`, `venue` (as parsed from the reference string), `cited_by_n_seeds`, `citing_seeds`, `possibly_already_screened` (flag raised by the script for a manual check), `author_decision`, `author_criterion`, `automated_decision`, `automated_criterion`, `automated_confidence` (high, medium, low), `automated_note`.

**`forward_screening.csv`** — the 637 forward candidates.
`sbid`, `eid`, `doi`, `title`, `authors`, `year`, `venue`, `cites_n_seeds`, `cites_which_seeds`, `citation_edge_status` (`CONFIRMED` when the seed was found in the citing paper's reference list, `NOT_FOUND_IN_PARSED_REFERENCES` otherwise), then the same decision columns as the backward file.

**`forward_removals.csv`** — citing records flagged for removal before screening. `reason` (seed matched by EID; already screened; matched to a backward candidate), `citing_title`, `matched_to`, `similarity`.

**`three_questions_automated.csv`** — automated coding of the three screening questions. `id`, `source` (database or forward), `q1_training`, `q2_distributed`, `q3_evidence` (Y, N, U), `pattern` (the three answers), `confidence`, `flags` (e.g. AGGREGATION-ONLY, BYZANTINE-ONLY, OUTSOURCED-SINGLE, UNLEARNING), `coded` (hand or batch), `note`.

**`three_questions_recheck_log.csv`** — answers changed when the automated coding was re-checked. `id`, `before`, `after`, `reason`.

**`three_questions_author.csv`** — the author's answers. `id`, `set` (QUERY-INCLUDED, QUERY-EXCLUDED, FORWARD), `q1_training`, `q2_distributed`, `q3_evidence`, `note`.

## 3_full_text

**`full_text_assessment.csv`** — every record kept by the three sources, with the outcome of the full-text stage.
`id`, `set` (Query, Backward, Forward), `year`, `title`, `venue`, `publication` (peer-reviewed, preprint, thesis, ...), `status` (Included; Remove = excluded, does not verify training; Remove (IC-1); Remove (EC-4); Duplicate; No full text; Not found; Not a paper; Query-excluded), `type` (for included studies), `criterion` (exclusion code in the paper's numbering), `criterion_source` (`recorded`, or `derived` from the recorded reason), `reason_or_note`.

**`full_texts_not_available.csv`** — studies whose full text could not be obtained. `id`, `also_listed_as`, `year`, `title`, `venue`, `doi_or_link`, `kind`.

**`borderline_rechecks.csv`** — classifications first marked unsure and how each was re-checked. `id`, `title`, `first_label`, `why_unsure`, `detail`, `how_rechecked`, `final_type`, `status`, `certainty`, `changed`, `note`.

## 4_included

**`included_studies.csv`** — the 125 included studies, one row each.
`id`, `set`, `authors`, `title`, `year`, `venue`, `doi`, `type`, `sub_type`, `scheme` (the name of the mechanism), `scope_level`, `scope_basis`, `who_checks`, `evaluation` (implemented, simulated, analytical, none), `largest_model`, `parameters_stated` (only where the study states it), `code_linked` (Y when the paper links to the authors' own code).

## 5_extraction

**`crypto_extraction.csv`** — the 54 cryptographic studies.
`id`, `scheme`, `sub_type`, `sub_type_decided_by`, `technique`, `what_the_proof_establishes`, `what_the_proof_covers`, `who_checks`, `model_class`, `largest_model_evaluated`, `evaluation`, `prototype_proves_less`, `claim` (what the paper claims), `setup` (trusted, transparent, ...), `verifier` (public or designated), `zero_knowledge`, `datasets`, `proving_cost_largest_experiment` (in the paper's own units, with pages), `trust_assumptions`.

**`noncrypto_extraction.csv`** — the 71 other studies.
`id`, `type`, `sub_type`, `scheme`, `evaluation` (Impl., Sim., Theory, None), `largest_model`, `parameters_stated`, `metrics` (codes), `hardware_named`, `code_released`, `where_in_paper`, `notes`.

**`crypto_metrics.csv`** — metrics each cryptographic study reports (Section 5.10 of the paper). `id`, `metrics` (codes), `added_from_full_text` (codes found in the full text beyond the proving-cost field), `where_in_paper`.

**`verification_scope.csv`** — scope level of all 125 studies (Section 6.1 of the paper). `id`, `type`, `who_checks`, `year`, `scope_level`, `basis`.

**`crypto_assumptions.csv`** — every trust assumption extracted from the 54 cryptographic studies. `id`, `status` (stated, unstated but needed), `assumption`, `group`, `data_tied_to_signer`.

**`crypto_assumptions_by_study.csv`** — one row per cryptographic study and assumption group: `stated` if any assumption in the group is stated, `not stated` if all are unstated but needed.

**`crypto_prototype_gap.csv`** — whether the evaluated prototype proves less than the paper specifies. `id`, `scheme`, `what_the_proof_covers`, `evaluation`, `gap_group`, `note`.

**`crypto_code_links.csv`** — `id`, `code_linked`, `link_as_given` (as printed in the paper).

**`crypto_limitations_qac5.csv`** — limitations discussed by each cryptographic study. `id`, `qac5` (Y, P, N), `limitations`, `pages`, `themes`.

**`crypto_fixed_point.csv`** — cryptographic studies that state fixed-point or quantised arithmetic for the proven computation. `id`, `evidence`.

**`model_sizes.csv`** — data of the model-size figure: studies stating the parameter count of the largest model they ran. `id`, `type`, `scope_level`, `year`, `parameters_stated`, `source` (the file the value comes from).
