#!/usr/bin/env python3
"""
Forward snowballing: process the papers that CITE the included studies of a
systematic literature review.

WHAT THIS SCRIPT DOES
  1. reads the Scopus "View cited by" export (with "Include references" ticked)
  2. reads the screening sheet, to know the included studies and everything
     already screened
  3. reads the backward-snowballing candidates, so nothing is screened twice
  4. for each citing paper, parses its reference list and records WHICH of the
     included studies it actually cites — an independent confirmation of the
     citation edge Scopus asserted
  5. removes citing papers that are themselves already screened, already a
     seed, or already a backward candidate
  6. writes a candidate list with EMPTY decision columns

WHY STEP 4 MATTERS
  Scopus returns "these papers cite your set" but not which paper cites which.
  Recovering the edge from the citing paper's own reference list gives
  provenance for every row and flags any paper where the claimed citation
  cannot be confirmed.

WHAT THIS SCRIPT DOES NOT DO
  It makes no inclusion or exclusion decisions.

USAGE
  pip install pandas
  python forward_snowball.py
"""

import csv
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher

import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
CITED_BY_EXPORT = "cited_by_export.csv"        # Scopus "View cited by" results
SCREENING_SHEET = "screening_sheet.csv"        # the 656 screened records
BACKWARD_CANDS  = "backward_candidates.csv"    # output of backward_snowball.py
OUTPUT          = "forward_candidates.csv"

COL_EID      = "EID"
COL_DECISION = "Decision"
COL_TITLE    = "Title"
COL_ID       = "ID"

FUZZY_THRESHOLD = 0.95   # title similarity at or above which two records are one work
BLOCK_LEN       = 9      # prefix/suffix length used to block candidate comparisons
MIN_TITLE_CHARS = 12     # shorter normalised titles are treated as parse fragments

INCLUDE_PREFIXES = ("include", "imclude", "inlcude", "includ")

# ----------------------------------------------------------------------------
# shared helpers (identical rules to backward_snowball.py, so the two passes
# deduplicate against each other consistently)
# ----------------------------------------------------------------------------

def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(text).lower())).strip()


def is_included(value) -> bool:
    return str(value).strip().lower().startswith(INCLUDE_PREFIXES)


REF_BOUNDARY = re.compile(r"(?<=\(\d{4}\))\s*;\s*")
VENUE_START = re.compile(
    r",\s*(?:pp?\.|\d+\s*(?:,|$)|\(\d{4}\)"
    r"|(?:Proceedings|Journal|IEEE|ACM|Advances|Lecture\s+Notes|Conference"
    r"|Transactions|Int\.|Proc\.|arXiv|CoRR|In)\b)"
)


def reference_titles(refs: str):
    """Yield the normalised title of every reference in a Scopus cell."""
    for ref in REF_BOUNDARY.split(str(refs)):
        ref = ref.strip()
        if len(ref) < 15:
            continue
        year = re.search(r"\((\d{4})\)\s*$", ref)
        body = ref[: year.start()].rstrip(" ,") if year else ref
        comma = body.find(",")
        if comma == -1:
            continue
        remainder = body[comma + 1:].strip()
        match = VENUE_START.search(remainder)
        title = (remainder[: match.start()] if match else remainder).strip().rstrip(",")
        key = normalise(title)
        if len(key) >= MIN_TITLE_CHARS:
            yield key


def same_work(a: str, b: str) -> bool:
    """Two normalised titles refer to the same work.

    Comparison is made on equal-length truncations, so trailing venue text on
    one side ("...for ML, Proc. ESORICS, pp. 3-23") cannot sink a title that is
    otherwise identical.

    A shared prefix is NOT treated as proof of identity. It is only a blocking
    signal used to select candidates for comparison. Two genuinely different
    papers can share a long prefix -- in this review, "Computational
    Attestations of Polynomial Integrity towards Verifiable Machine-Learning"
    and "...towards Verifiable Back-Propagation" agree for 60 characters but
    are separate studies (similarity 0.87). Treating the prefix as identity
    merged them and misattributed citations.
    """
    if a == b:
        return True
    n = min(len(a), len(b))
    if n < MIN_TITLE_CHARS:
        return False
    return SequenceMatcher(None, a[:n], b[:n]).ratio() >= FUZZY_THRESHOLD


def build_index(keys):
    """Block keys by head and tail so lookups do not scan everything."""
    index = defaultdict(list)
    for k in keys:
        index[k[:BLOCK_LEN]].append(k)
        index[k[-BLOCK_LEN:]].append(k)
    return index


def lookup(key, index):
    """Return the first indexed key that is the same work, or None."""
    for cand in set(index.get(key[:BLOCK_LEN], []) + index.get(key[-BLOCK_LEN:], [])):
        if same_work(key, cand):
            return cand
    return None


def main() -> None:
    try:
        cited = pd.read_csv(CITED_BY_EXPORT, dtype=str).fillna("")
        sheet = pd.read_csv(SCREENING_SHEET, dtype=str).fillna("")
    except FileNotFoundError as exc:
        sys.exit(f"Could not open {exc.filename} — check the paths in CONFIG.")

    try:
        backward = pd.read_csv(BACKWARD_CANDS, dtype=str).fillna("")
    except FileNotFoundError:
        backward = pd.DataFrame(columns=["title"])
        print("NOTE: backward_candidates.csv not found — skipping that overlap check.")

    missing = {COL_EID, COL_DECISION, COL_TITLE} - set(sheet.columns)
    if missing:
        sys.exit(f"Screening sheet is missing column(s): {sorted(missing)}")
    if "Title" not in cited.columns:
        sys.exit("The cited-by export has no 'Title' column.")

    has_refs = "References" in cited.columns
    if not has_refs:
        print("NOTE: the cited-by export has no 'References' column, so citation\n"
              "      edges cannot be confirmed. Re-export with 'Include references'\n"
              "      ticked to get provenance. Continuing without it.")

    # --- the included studies, and their titles -----------------------------
    included = sheet[sheet[COL_DECISION].map(is_included)]
    seed_title_to_id = {}
    for _, row in included.iterrows():
        key = normalise(row[COL_TITLE])
        if len(key) >= MIN_TITLE_CHARS:
            seed_title_to_id[key] = str(row.get(COL_ID, row[COL_EID])).strip()
    seed_index = build_index(seed_title_to_id)

    seed_eids = set(included[COL_EID])
    screened_titles = {normalise(t) for t in sheet[COL_TITLE] if normalise(t)}
    screened_index = build_index(screened_titles)
    backward_titles = {normalise(t) for t in backward.get("title", []) if normalise(t)}
    backward_index = build_index(backward_titles)

    print(f"included studies (seeds) : {len(included)}")
    print(f"citing papers returned   : {len(cited)}")

    # --- classify every citing paper ----------------------------------------
    rows = []
    n_seed = n_screened = n_backward = n_unconfirmed = 0
    for _, row in cited.iterrows():
        key = normalise(row["Title"])
        if len(key) < MIN_TITLE_CHARS:
            continue

        if row.get("EID", "") in seed_eids or lookup(key, seed_index):
            n_seed += 1
            continue                          # the paper is itself a seed
        if lookup(key, screened_index):
            n_screened += 1
            continue                          # already screened in the database search
        if lookup(key, backward_index):
            n_backward += 1
            continue                          # already a backward candidate

        # confirm the citation edge from this paper's own reference list
        cites = []
        refs_parsed = 0
        raw_refs = str(row.get("References", "")).strip()
        if has_refs and raw_refs:
            for ref_key in reference_titles(raw_refs):
                refs_parsed += 1
                hit = lookup(ref_key, seed_index)
                if hit:
                    cites.append(seed_title_to_id[hit])
            cites = sorted(set(cites))

        # Three outcomes, which are scientifically different and should not be
        # collapsed into one "not confirmed" bucket:
        if cites:
            status = "CONFIRMED"
        elif not has_refs or not raw_refs:
            status = "NO_REFERENCES_AVAILABLE"
        elif refs_parsed == 0:
            status = "REFERENCES_UNPARSEABLE"
        else:
            status = "NOT_FOUND_IN_PARSED_REFERENCES"
        if status != "CONFIRMED":
            n_unconfirmed += 1

        rows.append({
            "eid": row.get("EID", ""),
            "year": row.get("Year", ""),
            "authors": row.get("Authors", ""),
            "title": row["Title"],
            "venue": row.get("Source title", ""),
            "doi": row.get("DOI", ""),
            "cites_n_seeds": len(cites),
            "cites_which_seeds": "; ".join(cites),
            "refs_parsed": refs_parsed,
            "citation_edge_status": status,
        })

    print(f"  excluded — is a seed    : {n_seed}")
    print(f"  excluded — already screened : {n_screened}")
    print(f"  excluded — backward candidate: {n_backward}")

    out = pd.DataFrame(rows)
    if out.empty:
        sys.exit("No new candidates — check that the cited-by export is the right file.")

    out = out.sort_values(["cites_n_seeds", "year"],
                          ascending=[False, False]).reset_index(drop=True)
    out.insert(0, "SBID", [f"F{i:04d}" for i in range(1, len(out) + 1)])
    out["DECISION"] = ""
    out["CRITERION"] = ""
    out["NOTE"] = ""
    out = out[["SBID", "eid", "doi", "year", "authors", "title", "venue",
               "cites_n_seeds", "cites_which_seeds", "citation_edge_status",
               "refs_parsed", "DECISION", "CRITERION", "NOTE"]]
    out.to_csv(OUTPUT, index=False, quoting=csv.QUOTE_ALL)

    print()
    print(f"NEW CANDIDATES TO SCREEN : {len(out)}")
    if has_refs:
        from collections import Counter
        for k, v in Counter(candidates := out.citation_edge_status).most_common():
            print(f"   {k:32}: {v}")
    print(f"written to               : {OUTPUT}")
    print()
    print(f"parameters: FUZZY_THRESHOLD={FUZZY_THRESHOLD} BLOCK_LEN={BLOCK_LEN} "
          f"MIN_TITLE_CHARS={MIN_TITLE_CHARS}")


if __name__ == "__main__":
    main()
