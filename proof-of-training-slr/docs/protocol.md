# Review protocol

This file restates the protocol of the review as applied. Section numbers refer to the paper.

## Research questions (Section 3.1)

**RQ1. What mechanisms let one party establish to another that a model was trained as claimed?**

- RQ1.1 What trust basis does each rely on (cryptographic proof, trusted hardware, statistical replay, consensus)?
- RQ1.2 How is each built (proof system, what is committed, how training steps are encoded)?
- RQ1.3 In which settings is it used, and who checks (delegated training, federated learning, data marketplace, blockchain consensus)?

**RQ2. What do these mechanisms actually establish?**

- RQ2.1 Which parts of training does each mechanism verify (verification scope)?
- RQ2.2 Under which threat model and assumptions (trusted setup, honest data source, quantised arithmetic, honest verifier, collusion limits)?
- RQ2.3 How mature is the evidence (models, datasets, scale), and at what cost (prover time, proof size, verification time, memory)?

**RQ3. What challenges and research opportunities follow from the findings of RQ1 and RQ2?**

## Inclusion criteria (all must hold)

| Code | Criterion |
|---|---|
| IC-1 | Primary, peer-reviewed study (full journal, conference or workshop paper) |
| IC-2 | What is verified is the training process or its inputs: the training computation, the data used in training, or the fact that the model came from training |
| IC-3 | Proposes, analyses or attacks a mechanism that produces evidence a second party can check |
| IC-4 | Written in English, full text available |
| IC-5 | Published 2021 or later (database search only; snowballed papers of any year are kept) |

## Exclusion criteria (any one excludes)

Exclusion criteria are applied in numerical order; each excluded record carries the first criterion that applies.

| Code | Criterion |
|---|---|
| EC-1 | Duplicate, demo, or earlier or extended version of an included study (the most complete version is kept) |
| EC-2 | Not about machine learning training |
| EC-3 | Secondary study: survey, review or SoK |
| EC-4 | Not a full paper: thesis, proposal, work in progress, short or vision paper, keynote or abstract |
| EC-5 | What is verified is not training: inference only, gradient transport, node identity, or an unrelated use of "proof" |
| EC-6 | Ownership or IP protection only (watermark, fingerprint, dataset inference), with no claim about the training process |
| EC-7 | *Dropped during the review* (see [rulings.md](rulings.md)): guarantee rests only on trusted hardware |
| EC-8 | Not written in English |

## Criteria numbering at screening

Title and abstract screening (September 2026) used an earlier numbering of the same criteria. The screening files keep the codes as recorded. Two codes differ from the paper:

| Code in the screening files | Meaning | Code in the paper |
|---|---|---|
| EC-2 | Not written in English | EC-8 |
| IC-2 | Proposes, analyses or evaluates a mechanism by which one party can establish to another that a model was trained as claimed (recorded when the subject is right but no claim to a second party is made) | IC-3 |
| IC-3 | Full text accessible | IC-4 |

EC-1, EC-3, EC-4, EC-5, EC-6 and EC-7 have the same meaning in both. The paper's EC-2 (not about machine learning training) was added after screening; at screening such records were coded EC-5. `TEE` in the database screening marks a trusted-hardware record kept as borderline because its root of trust could not be judged from the abstract.

## Selection

1. **Title and abstract.** Every record from the database search was screened against the criteria. Records whose eligibility could not be judged from the abstract were carried forward as borderline (`include-borderline`) rather than excluded; this applied in particular to mechanisms relying on trusted hardware, whose root of trust abstracts rarely state. See [screening.md](screening.md).
2. **Snowballing.** One round of backward and forward snowballing, seeded from the 114 records kept at title and abstract screening. Candidates were screened against the same criteria, except IC-5. See [screening.md](screening.md).
3. **Full text.** The full text of every retained study was read against the same criteria. Questions that arose were settled by written rulings applied to every affected study ([rulings.md](rulings.md)).

## Quality assessment (Section 3.4)

Each criterion is scored yes = 1, no = 0. A study must meet QAC-2 to remain in the review; the other four criteria are reported but do not exclude.

| Code | Criterion |
|---|---|
| QAC-1 | The research objective or problem is clearly stated |
| QAC-2 | The proposed mechanism is described in enough detail to be understood |
| QAC-3 | The guarantee is stated: what is proven, and under which assumptions |
| QAC-4 | An evaluation is reported: empirical measurement, formal analysis, or both |
| QAC-5 | Limitations or threats to validity are discussed |

## Extraction form (Section 3.6)

| Field | Values recorded | RQ |
|---|---|---|
| Type (trust basis) | Cryptographic proof, math check, trusted hardware, runtime behaviour, redo the work, model behaviour, work puzzle, incentives; aggregation-only proof as a ninth type | RQ1.1 |
| Sub-type and technique | e.g. proof-system family (circuit SNARK, sum-check/GKR, zkVM, VOLE/MPC-in-the-head, proofs on committed values) and the system named in the paper | RQ1.2 |
| Construction | What is committed, and how training steps are encoded | RQ1.2 |
| Setting and verifier | Delegated training, federated learning, data marketplace, blockchain; who checks (single verifier, server, validators, peers, clients) | RQ1.3 |
| Verification scope | What is verified and how much of training (Full, Sampled, Partial, Related step or Not detailed) | RQ2.1 |
| Assumptions | Trusted setup, honest data source, quantised arithmetic, honest verifier, collusion limits, determinism | RQ2.2 |
| Evaluation | Model, dataset, largest model (parameters), evaluation type (measured, simulated, analytical, none) | RQ2.3 |
| Cost | Prover time, proof size, verification time, memory, hardware | RQ2.3 |
| Stated limitations | As written by the authors | RQ3 |
| Quality | QAC-1 to QAC-5 | Sec. 3.4 |

Each value was recorded as the paper states it, with the page it comes from. Costs are kept in the paper's own units together with the hardware used; a value a paper does not report is recorded as not reported, never estimated. Parameter counts are recorded only where a paper states them.
