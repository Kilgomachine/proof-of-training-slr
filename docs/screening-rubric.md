# Screening rubric

This is the written rubric that the automated screening pass applied to the snowballing candidates (September 2026). The 656 database records were screened by the same pass under the same criteria and central test; this version adds the title-only rule for backward candidates, which carry no abstract. It is kept verbatim as a record and is phrased as instructions to the screener.

Two things changed after screening (see [rulings.md](rulings.md)): proofs that cover only the aggregation step, tagged `[SCOPE: aggregation]` and coded EC-5 here, were later included as a ninth type; and EC-7 (trusted hardware only) was dropped. The criterion numbering is the one used at screening; [protocol.md](protocol.md#criteria-numbering-at-screening) maps it to the paper's numbering.

---

## Rubric

Same review, same criteria as the 656 database records. Two differences matter:

  FORWARD candidates (F####)  have abstracts. Screen them exactly as the 656.
  BACKWARD candidates (B####) have TITLE ONLY — a reference string carries no
                              abstract. You are screening on less information,
                              so the bar for excluding must be higher (below).

## Scope
Machine learning + proof of training. No restriction on model type.

## THE CENTRAL TEST
**What is the OBJECT of the proof or verification, and does that object
PRODUCE or UPDATE model weights?**

    yes -> it is training          -> candidate for include
    no  -> it is not training      -> EC-5

Worked calls:
    gradient computed from committed data    produces weights   include
    aggregation of client updates            produces weights   include
    gradient NORM bound                      property of value  EC-5
    signatures on transmitted gradients      transport          EC-5
    node identity / access control           identity           EC-5
    model outputs / predictions              inference          EC-5
    deployed model behaviour                 deployment         EC-5
    device firmware integrity                attestation        EC-5
    answers, reasoning steps, rewards        ML scoring         EC-5

Rigour is IRRELEVANT. A formally sound Lyapunov certificate or a deterministic
rule checker still fails EC-5 if its object is not training.

## ORDERING — lowest-numbered criterion that fires WINS. Never stack codes.
EC-1..EC-4 = what the ARTIFACT is. EC-5..EC-7 = what the CONTENT says.
All EC before any IC.

EC-1  Duplicate, or an extended version of another included study.
EC-2  Not in English.
EC-3  Secondary study: survey, review, systematic mapping, SoK.
EC-4  Not a full peer-reviewed paper: book, thesis, tech report, keynote,
      panel, editorial, poster, extended abstract, doctoral symposium.
EC-5  The verification target is not training.
EC-6  Watermarking/fingerprinting for ownership or IP rather than establishing
      how the model was trained.
EC-7  Correctness rests ENTIRELY on a trusted third party or trusted hardware,
      with no verifiable argument. TEST: strip out every trusted party and
      chip — is a checkable argument left? EC-7 only applies when the target
      IS training. Object first, always.

IC-1  Peer-reviewed journal, conference or workshop paper.
IC-2  Proposes, analyses or evaluates a MECHANISM by which one party can
      establish to another that an ML model was trained as claimed.
      Reserved for RIGHT SUBJECT, NO CLAIM to a second party.
IC-3  Full text accessible. Assume yes unless clear evidence otherwise.

## TITLE-ONLY RULE — backward candidates (B####) ONLY
You cannot see the abstract. Therefore:
  * Exclude only when the TITLE ALONE is decisive. "Bitcoin: A peer-to-peer
    electronic cash system", "ImageNet", "Very deep convolutional networks",
    "Attention is all you need" — decisive, exclude.
  * When the title is about ML + verification/proof but the OBJECT is not
    stated in it, use **include-borderline**, not exclude. A title like
    "Verifiable Federated Learning with zk-SNARKs" does not say whether the
    proof covers training or aggregation or transport — you cannot know.
  * Rationale: a wrong exclude here deletes a paper from the review silently.
    A wrong include costs one abstract read later. The errors are not
    symmetric, so under-exclude.

## CONNECTIVITY IS NOT ELIGIBILITY
`cited by N of the 114` / `cites N of the included studies` measures how
connected a paper is, NOT whether it belongs. Surveys cite everything and are
still EC-3. Foundational ML papers (FedAvg, Groth16, CIFAR) are cited by
dozens of your studies and are still EC-5. Judge the paper, not the number.

## DECISION VOCABULARY — exactly one of these four strings
include              clearly in scope
include-borderline   in, but depends on an unresolved rule or needs full text
exclude              clearly out
exclude-borderline   out, but flagged as worth a second look
CRITERION: blank for includes; filled only on exclusions.

## OPEN SCOPE TAGS — tag the note, do not decide
[SCOPE: aggregation]  proof covers FL aggregation only, not local gradients
                      (the lead has ruled these OUT — code EC-5 and tag)
[SCOPE: TEE]          target IS training but the root of trust is hardware
                      (deferred to full text — include-borderline and tag)
[SCOPE: unlearning]   proof covers machine unlearning (undecided — borderline)

## KNOWN NOISE CLASSES (all EC-5 unless a lower criterion fires)
- Privacy-preserving federated learning: ZKP/HE secures transport, identity or
  norms, never the computation. The single largest class.
- ML-sense "verification": verifier = a model or heuristic scoring outputs,
  reasoning steps or rewards. RLVR/RLVF, LLM-as-judge, process reward models.
- Verifiable inference / zkML: proves a model ran on an input.
- Authentication / biometrics / identity / access control.
- Formal methods: SAT/QBF/proof complexity, theorem provers, CEGIS
  ("learner-verifier"), Lyapunov certificates. "Learning" = clause learning.
- Lattice cryptography: matched on "learning with errors/rounding".
- Human education: "learner" = student, "training" = staff training.
- ML-as-instrument: the contribution is something else and ML is a helper.
- Foundational ML/crypto cited as background: FedAvg, Groth16, ImageNet,
  CIFAR, Bitcoin, VGG, Bulletproofs, Nova.

## OUTPUT — strict TSV, one line per paper, no header, no commentary
ID<TAB>DECISION<TAB>CRITERION<TAB>NOTE<TAB>CONFIDENCE
NOTE: one line, under 15 words, no tabs. Say what the paper IS.
CONFIDENCE: high | medium | low. Use low honestly — for backward candidates,
low should be common, because a title often does not say what the proof covers.
Output every ID in your batch, in order. Skip nothing.
