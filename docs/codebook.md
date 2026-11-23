# Codebook

The values used in the extraction files ([data-dictionary.md](data-dictionary.md) lists the files and columns).

## Type

Each study has exactly one type: what its guarantee rests on, except that proofs covering only the aggregation step form a ninth type defined by that narrower scope.

| Type | What the guarantee rests on | Studies |
|---|---|---|
| Cryptographic proof | A proof the verifier checks (zero-knowledge proof, SNARK, zkVM, sigma protocol), whose soundness rests on a hardness assumption | 54 |
| Redo the work | Someone other than the trainer re-runs all or part of the training and compares the result | 22 |
| Trusted hardware | A trusted execution environment runs or re-executes the training and attests the result | 10 |
| Model behaviour | A statistical test on the model, its updates or its outputs (planted probes, canaries, weight statistics) | 9 |
| Work puzzle | Training is the mining puzzle: verifiers measure the result against a target, as in proof of work | 7 |
| Math check | An algebraic or interactive check that needs no hardness assumption (Freivalds-type test, MAC check over a field, rank certificate, PAC verification) | 5 |
| Runtime behaviour | A record of how the training code ran (control flow, variable use, counters) is compared with what the expected code would produce | 2 |
| Incentives | Payments, stakes or penalties make cheating unprofitable; the check itself is borrowed | 1 |
| Aggregation-only proof | A proof, hash check or committee that covers only the server's aggregation of client updates; local training is not checked | 15 |

Attack and analysis studies are classified by the scheme they target, and tools by the check they enable (ruling F).

## Sub-type

| Type | Sub-types (studies) |
|---|---|
| Cryptographic proof | Circuit SNARKs (30); Proofs on committed values (9); Sum-check / GKR (6); zkVMs (6); VOLE / MPC-in-the-head (3) |
| Redo the work | A verifier or auditor re-runs logged training (10); Blockchain participants re-run training (6); Attacks and analyses of replay (3); Reproducibility tools for replay (2); Peers recompute each other's steps (1) |
| Trusted hardware | Training runs inside the enclave (5); Enclave re-executes sampled training (3); Enclave with checked GPU offloading (2) |
| Model behaviour | Tests on updates or checkpoints (3); Inference about the training data (3); Planted samples or probes (2); Contribution tests on updates (1) |
| Work puzzle | Accuracy target on data the miners hold (3); Accuracy target on data released after commitment (3); Weight-movement target (1) |
| Math check | PAC verification of the outcome (2); Algebraic certificate on a training step (1); Information-theoretic MAC check (1); Randomised check of outsourced linear algebra (1) |
| Runtime behaviour | Control-flow and variable-use trace (1); Control-flow counts and hardware counters (1) |
| Incentives | Reward and audit-probability design (1) |
| Aggregation-only proof | Homomorphic hashes, commitments or signatures (7); ZK proof of the aggregation (6); Blockchain committee or ledger (2) |

Cryptographic sub-types follow the proof system named in the paper; where a paper names none, it was placed by the circuit it describes or the systems it cites (`sub_type_decided_by`).

## Verification scope

How much of the training the mechanism checks, as the study specifies it.

| Level | Meaning | Studies |
|---|---|---|
| Full | Every training step (forward pass, backward pass and update) is proven, re-run or executed inside an enclave | 40 |
| Sampled | A random or selected subset of steps, each checked in full | 19 |
| Partial | Part of the computation of each step, such as the forward pass, some layers or the outsourced matrix products | 13 |
| Related step | A step around training rather than training itself: the aggregation of updates, the outcome (accuracy, or distance from the optimum), a property of the model or its updates (a norm bound, a statistical test), or knowledge of committed values | 43 |
| Not detailed | The study does not say which computation its proof covers, or borrows the check from elsewhere | 10 |

`scope_basis` gives the reason for the level. For cryptographic proofs, `what_the_proof_covers` in `crypto_extraction.csv` uses finer values: Every training step; Sampled steps, each in full; Part of the training; Forward pass only; The outcome only; A norm bound only; A commitment or knowledge only; Relation not given or only sketched by the authors; Borrowed proofs.

## Who checks

`Single verifier` (a client, auditor or model owner; 47), `FL server` (33), `Blockchain` (validators, miners or a smart contract; 30), `FL clients` (10, aggregation-only proofs), `Peers` (5).

## Evaluation

`implemented` (the mechanism was built and run), `simulated` (no real training or system), `analytical` (formal results only), `none` (no evaluation reported). The extraction files keep the original labels: `measured`, `simulated`, `analytical only`, `none` for cryptographic proofs and `Impl.`, `Sim.`, `Theory`, `None` for the other types.

## Metrics

Codes of the metric catalogue (Table 9 of the paper), used in `crypto_metrics.csv` and `noncrypto_extraction.csv`. A metric is coded only where the study reports a value, not where it only mentions the metric.

| Code | Metric |
|---|---|
| PT | Prover time (time to produce the evidence) |
| VT | Verification time |
| PS | Proof or evidence size (stored proofs or evidence included) |
| ST | Setup time |
| MEM | Memory |
| COM | Communication (volume or time) |
| CHAIN | On-chain cost (gas, block time, fork rate) |
| OVH | Overhead vs. plain training (needs a comparison with training without the mechanism) |
| ACC | Accuracy or loss, when a result of the evaluation (with vs. without the mechanism, under attack, or across runs); reward for bandit and reinforcement learners |
| DET | Detection or verification outcome, including the success of attacks on integrity; outcomes of privacy attacks are not coded |
| CONF | Soundness or confidence, when a probability is reported |
| SAMP | Sample or query complexity |
| ENERGY | Energy (outside the catalogue) |

## Trust assumptions (cryptographic proofs)

Each assumption in `crypto_assumptions.csv` is `stated` by the study or `unstated but needed` for its guarantee, and placed in one group: Trusted setup or key authority; Honest data source; Trusted server, coordinator or verifier; Honest majority or bounded collusion; Unbiased randomness; Unchecked input, off-chain step or program; Rational participants; Determinism or arithmetic bounds. Four further groups are recorded but not counted: Standard cryptographic; Privacy only; Not about soundness; Other.

## Prototype gap (cryptographic proofs)

Whether the evaluated prototype proves what the paper specifies: `No gap`; `Proves a smaller or different statement`; `Omits a component or extrapolates the cost`; `No proof generated`; `Cannot be determined`.

## Quality

QAC-5 (limitations discussed) is recorded as `Y` (discussed), `P` (partly: only some limitations, or only future work) or `N` (not discussed).
