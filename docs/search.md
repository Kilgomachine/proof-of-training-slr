# Search

## Database and execution

- **Database:** Scopus (Advanced search, field `TITLE-ABS-KEY`).
- **Executed and frozen:** 16 September 2026, 656 records. All counts in the paper refer to this frozen set. Re-executing the identical query nine days later returned 661 records.
- **Filters:** publication year after 2020; document type article (`ar`) or conference paper (`cp`); English.
- **Query:** [`data/1_search/scopus_query.txt`](../data/1_search/scopus_query.txt) (the paper prints the same string as Figure 1).
- **Records:** [`data/1_search/database_records.csv`](../data/1_search/database_records.csv) lists the 656 records with their Scopus EID, DOI and bibliographic fields. IDs `P001` to `P656` are used throughout the package and the paper.

To re-obtain the full Scopus records (abstracts, keywords, reference lists), which this package does not redistribute, run the query again in Scopus, or search the 656 EIDs (`EID(2-s2.0-...) OR ...`), and export as CSV with all fields and references.

## Query construction

The query has two blocks joined by AND.

1. **Verification of training.** Verification terms (`proof*, prove, proves, proving, proven, verif*, attest*, certif*, audit*, watermark*`) within five words (`W/5`) of training terms (`train*, learn*, "gradient descent", SGD, fine-tun*, finetun*, distill*`). The proximity constraint separates a record asserting that a trained model was verified from one that merely mentions both subjects.
2. **Proof machinery present.** At least one of: `prover, verifier, "proof system", soundness, "zero-knowledge", "zero knowledge", zkSNARK, SNARK, "trusted execution", "secure enclave", "proof-of-learning", "proof of learning", "proof-of-training", "proof of training", nondeterminis*, "non-deterministic", "refereed delegation"`.

## Validation set

Six studies were fixed in advance; a refinement step was rejected if the query stopped returning any of them. The final query returns all six, and all six were retained at screening. See [`data/1_search/validation_set.csv`](../data/1_search/validation_set.csv).

| ID | Study | Venue |
|---|---|---|
| P303 | Experimenting with Zero-Knowledge Proofs of Training | ACM CCS 2023 |
| P497 | Zero-Knowledge Proofs of Training for Deep Neural Networks | ACM CCS 2024 |
| P424 | zkDL: Efficient Zero-Knowledge Proofs of Deep Learning Training | IEEE TIFS 2025 |
| P333 | Founding Zero-Knowledge Proofs of Training on Optimum Vicinity | ACM CCS 2025 |
| P600 | Proof-of-Learning: Definitions and Practice | IEEE S&P 2021 |
| P143 | Optimistic Verifiable Training by Controlling Hardware Nondeterminism | NeurIPS 2024 |

## Refinement record

The record kept during query construction (hits in Scopus at each step; recall = how many of the six validation studies the query returned):

| Step | Change | Hits | Recall |
|---|---|---|---|
| 1 | Initial three-axis query: claim words AND training words AND threat words | 35,106 | — |
| 2 | Proximity (`W/5`) binds the claim words to the training words | 9,197 | — |
| 3 | `watermark*` removed (37% of the results) | 3,784 | — |
| 4 | Broad compliance vocabulary removed (`licens*`, `copyright`, `consent`, `governance`, `compliance`, `"differentially private"`, `"membership inference"`) | 1,133 | 1/6 |
| 5 | Threat axis deleted (it excluded the target literature, not the noise); `prove, proves, proving, proven` added; `learn*` restored, since its removal had made "proof-of-learning" unfindable | 36,818 | 6/6 |
| 6 | Third axis rebuilt from protocol vocabulary (`prover, verifier, soundness, zero-knowledge` in place of `malicious, untrusted, byzantine, outsourced`) | 2,007 | 4/6 |
| 7 | Named escapes for non-cryptographic families: `"proof-of-learning"`, `"proof of training"`, `nondeterminis*`, `reproducib*`, `"refereed delegation"` (Proof-of-Learning and Optimistic Verifiable Training use no cryptography and had dropped out at step 6) | 3,053 | 6/6 |
| 8 | Document type (article, conference paper) and language (English) limits | 2,670 | 6/6 |
| 9 | `watermark*` restored, now bound by the proximity operator (3,404 when unconstrained at step 3) | 2,728 | 6/6 |

The narrative of the record gives 5,793 hits for step 3, against 3,784 in its summary table.

**Final edits before execution.** From the step-9 query, the second block dropped `commitment`, `cryptograph*` and `reproducib*`, and the filter `PUBYEAR > 2020` was added. The resulting query returned the 656 records of 16 September 2026, with 6/6 recall. Hits for these final edits were not recorded separately.

## Forward snowballing seeds

Scopus does not run a cited-by search over 114 records at once, so the 114 seeds were queried in three blocks of 40, 40 and 34 EIDs: [`data/1_search/forward_snowballing_seed_blocks.txt`](../data/1_search/forward_snowballing_seed_blocks.txt). Run each block, combine the result sets, then use "View cited by" and export.
