# Proof of Training: A Systematic Literature Review — replication package

This repository holds the data and scripts behind the systematic literature review *Proof of Training: A Systematic Literature Review*. It covers every stage: the search, the screening of 3,942 records, the full-text assessment and the extraction of the 125 included studies. With it, the selection and the counts reported in the paper can be checked, repeated and extended.

## Contents

| Folder | What it holds |
|---|---|
| [`docs/`](docs) | Protocol, search and refinement record, screening rubric, written rulings, codebook, AI assistance, data dictionary |
| [`data/1_search/`](data/1_search) | The Scopus query, the 656 records it returned, the validation set, the forward-snowballing seed blocks |
| [`data/2_screening/`](data/2_screening) | Title and abstract decisions for the 656 database records, 2,649 backward and 637 forward candidates, with the automated pass's decisions and the three-question cross-check |
| [`data/3_full_text/`](data/3_full_text) | The outcome of full-text reading for every record kept, with the reason for each exclusion |
| [`data/4_included/`](data/4_included) | The 125 included studies with their classification |
| [`data/5_extraction/`](data/5_extraction) | Extracted data: cryptographic proofs, other types, verification scope, trust assumptions, metrics, prototype gaps, code links, limitations, model sizes |
| [`scripts/`](scripts) | Snowballing and coverage scripts, and a script that recomputes the paper's counts |

Start with [`docs/protocol.md`](docs/protocol.md) for the method and [`docs/data-dictionary.md`](docs/data-dictionary.md) for the files.

## Where the paper's numbers come from

| In the paper | File |
|---|---|
| Search string and refinement (Section 3.3) | [`data/1_search/scopus_query.txt`](data/1_search/scopus_query.txt), [`docs/search.md`](docs/search.md) |
| Selection flow (Figure 2) and agreement figures (Sections 3.4–3.5) | [`data/2_screening/`](data/2_screening), [`data/3_full_text/full_text_assessment.csv`](data/3_full_text/full_text_assessment.csv), [`docs/screening.md`](docs/screening.md) |
| Written rulings (Section 3.4) | [`docs/rulings.md`](docs/rulings.md) |
| Types, sub-types and who checks (Section 5) | [`data/4_included/included_studies.csv`](data/4_included/included_studies.csv) |
| Cryptographic sub-types, comparison tables and cost (Sections 5.1 and 6.3) | [`data/5_extraction/crypto_extraction.csv`](data/5_extraction/crypto_extraction.csv) |
| Metrics reported per type (Section 5.10) | [`data/5_extraction/crypto_metrics.csv`](data/5_extraction/crypto_metrics.csv), [`data/5_extraction/noncrypto_extraction.csv`](data/5_extraction/noncrypto_extraction.csv) |
| Verification scope (Section 6.1) | [`data/5_extraction/verification_scope.csv`](data/5_extraction/verification_scope.csv) |
| Assumptions (Section 6.2) | [`data/5_extraction/crypto_assumptions.csv`](data/5_extraction/crypto_assumptions.csv), [`crypto_assumptions_by_study.csv`](data/5_extraction/crypto_assumptions_by_study.csv), [`crypto_fixed_point.csv`](data/5_extraction/crypto_fixed_point.csv) |
| Maturity: prototype gaps, model sizes, code (Section 6.3) | [`crypto_prototype_gap.csv`](data/5_extraction/crypto_prototype_gap.csv), [`model_sizes.csv`](data/5_extraction/model_sizes.csv), [`crypto_code_links.csv`](data/5_extraction/crypto_code_links.csv) |
| Limitations (Section 7) | [`data/5_extraction/crypto_limitations_qac5.csv`](data/5_extraction/crypto_limitations_qac5.csv) |

To recompute the main counts (Python 3, standard library only):

```
python scripts/reproduce_numbers.py
```

It prints each count from the data next to the value in the paper.

## Repeating the search and snowballing

1. Run the query in [`data/1_search/scopus_query.txt`](data/1_search/scopus_query.txt) in Scopus Advanced search, or retrieve the 656 records of the frozen set by their EIDs ([`database_records.csv`](data/1_search/database_records.csv)). Export as CSV with all fields and references.
2. Backward snowballing: [`scripts/snowballing/backward_snowball.py`](scripts/snowballing/backward_snowball.py) on that export.
3. Forward snowballing: run the three EID blocks in [`forward_snowballing_seed_blocks.txt`](data/1_search/forward_snowballing_seed_blocks.txt), export the cited-by results, then run [`forward_snowball.py`](scripts/snowballing/forward_snowball.py) and [`verify_forward_coverage.py`](scripts/snowballing/verify_forward_coverage.py).

[`scripts/README.md`](scripts/README.md) gives the inputs and outputs of each script.

## What is not included

- **Full texts** of the studies: they are under the publishers' copyright. The DOIs in [`included_studies.csv`](data/4_included/included_studies.csv) lead to them.
- **Scopus abstracts, keywords, affiliations and reference lists**: Scopus content is not redistributed. The files keep bibliographic identifiers (EID, DOI, title, authors, venue, year), from which the full records can be re-exported.

## AI assistance

A large language model was used as a second screener and as a coding assistant; every inclusion decision is the author's. [`docs/ai-assistance.md`](docs/ai-assistance.md) records what the model and the author did at each stage, and where each result is.

## Licence

Data and documentation: Creative Commons Attribution 4.0 International ([`LICENSE`](LICENSE)). Scripts: MIT ([`scripts/LICENSE`](scripts/LICENSE)).
