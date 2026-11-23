#!/usr/bin/env python3
"""
Backward snowballing: extract, deduplicate and cross-check the reference lists
of the included studies of a systematic literature review.
Version 2.

WHAT THIS SCRIPT DOES
  1. reads a Scopus CSV export produced with "Include references" ticked
  2. keeps only the studies marked included in the screening sheet
  3. splits each study's reference list into individual references
  4. parses author / title / year out of each reference string
  5. deduplicates by normalised title, then by fuzzy match, using union-find
     so that merging is transitive and independent of row order
  6. counts, for each work, the number of UNIQUE included studies citing it
  7. removes works already screened in the database search (exact + fuzzy)
  8. writes a candidate list ordered by that count, with EMPTY decision columns

WHAT THIS SCRIPT DOES NOT DO
  It makes no inclusion or exclusion decisions. Every candidate it outputs must
  still be screened by hand against the review's IC/EC criteria.

REPORTABLE PARAMETERS
  FUZZY_THRESHOLD, BLOCK_LEN, MIN_TITLE_CHARS and the INCLUDE_PREFIXES list are
  the choices that affect the output. Report them in the methodology.

USAGE
  pip install pandas
  python backward_snowball.py
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
SCOPUS_WITH_REFS = "export_with_references.csv"
SCREENING_SHEET  = "screening_sheet.csv"
OUTPUT           = "backward_candidates.csv"

COL_EID      = "EID"
COL_DECISION = "Decision"
COL_TITLE    = "Title"
COL_ID       = "ID"      # your own paper IDs (P001 ...). Optional; falls back to EID.

FUZZY_THRESHOLD = 0.95   # title similarity at or above which two records are one work
BLOCK_LEN       = 9      # prefix length used to block fuzzy comparisons
MIN_TITLE_CHARS = 12     # shorter normalised titles are treated as parse fragments
PREFIX_LEN      = 60     # leading characters compared when matching against the
                         # already-screened titles (absorbs trailing venue text)

# Decision values that mean "included". Matched case-insensitively against the
# start of the cell, so "Include", "include-borderline" and the typo "Imclude"
# all pass, while "ineligible" or "irrelevant" do NOT.
INCLUDE_PREFIXES = ("include", "imclude", "inlcude", "includ")

# ----------------------------------------------------------------------------
# text handling
# ----------------------------------------------------------------------------

def normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace. For matching only."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def is_included(value) -> bool:
    v = str(value).strip().lower()
    return v.startswith(INCLUDE_PREFIXES)


# Scopus separates references with "; " and ALSO separates authors inside a
# reference with "; ". The reliable boundary is the closing "(YYYY)" that ends
# each reference, so split only on a semicolon that follows one.
#
# The lookbehind "(?<=\(\d{4}\))" is fixed width: "(" + exactly four digits +
# ")" = 6 characters. The variable-width "\s*;\s*" is the matched text, outside
# the assertion, so this compiles and runs correctly.
REF_BOUNDARY = re.compile(r"(?<=\(\d{4}\))\s*;\s*")

# Where the title stops and the venue/volume/pages begin.
VENUE_START = re.compile(
    r",\s*(?:pp?\.|\d+\s*(?:,|$)|\(\d{4}\)"
    r"|(?:Proceedings|Journal|IEEE|ACM|Advances|Lecture\s+Notes|Conference"
    r"|Transactions|Int\.|Proc\.|arXiv|CoRR|In)\b)"
)


def parse_reference(ref: str):
    """Return (authors, title, venue, year) for one Scopus reference string.

    Scopus emits two author styles and both must be handled:
        "Abbaszadeh K.; Pappas C.; Katz J., Title, Venue, ..."   initials
        "Groth Jens, Title, Venue, ..."                          full names
    In both, author names contain no commas, so the author list ends at the
    first comma in the reference. Version 1 of this script required trailing
    initials and mis-parsed 10.6% of references, putting the author list into
    the title field.
    """
    ref = ref.strip()
    year_match = re.search(r"\((\d{4})\)\s*$", ref)
    year = year_match.group(1) if year_match else ""
    body = ref[: year_match.start()].rstrip(" ,") if year_match else ref

    comma = body.find(",")
    if comma == -1:
        return "", body.strip(), "", year

    authors = body[:comma].strip()
    remainder = body[comma + 1:].strip()

    # Split the remainder into title and venue. Keeping the venue OUT of the
    # title matters: a title carrying its venue will not match the same paper's
    # title in the screening sheet, and already-screened works leak back in.
    match = VENUE_START.search(remainder)
    if match:
        title = remainder[: match.start()].strip().rstrip(",")
        venue = remainder[match.start():].lstrip(", ").strip()
    else:
        title, venue = remainder.strip().rstrip(","), ""
    return authors, title, venue, year


def same_work(a: str, b: str) -> bool:
    """Two normalised titles refer to the same work.

    Compared on equal-length truncations, so trailing venue text on one side
    cannot sink an otherwise identical title.

    A shared prefix is NOT proof of identity, only a blocking signal. Two
    different studies in this review share 60 leading characters
    ("Computational Attestations of Polynomial Integrity towards Verifiable
    Machine-Learning" vs "...towards Verifiable Back-Propagation", similarity
    0.87); treating the prefix as identity merged them.

    This function is deliberately identical to the one in forward_snowball.py:
    both passes must agree about what counts as the same work, or a paper can
    be removed from one list and kept in the other.
    """
    if a == b:
        return True
    n = min(len(a), len(b))
    if n < MIN_TITLE_CHARS:
        return False
    return SequenceMatcher(None, a[:n], b[:n]).ratio() >= FUZZY_THRESHOLD


# ----------------------------------------------------------------------------
# union-find, so that fuzzy merging is transitive and order-independent
# ----------------------------------------------------------------------------

class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def fuzzy_clusters(keys, threshold, block_len, prefix_len):
    """Group keys that refer to the same work.

    Two rules, both needed:
      * exact agreement on the first `prefix_len` characters. Reference titles
        sometimes carry trailing venue text that the title/venue split missed,
        so "zkCNN: ..." and "zkCNN: ..., Proc. IEEE S&P, pp. 2968-2985" are one
        work but score poorly on whole-string similarity.
      * similarity >= `threshold` within blocks keyed on the first and last
        `block_len` characters, which catches ordinary formatting drift.

    Union-find makes the result transitive and independent of row order.
    """
    uf = UnionFind(keys)

    # A shared prefix selects candidates for comparison; it does not by itself
    # merge them. same_work() still has to agree.
    by_prefix = defaultdict(list)
    for k in keys:
        if len(k) >= prefix_len:
            by_prefix[k[:prefix_len]].append(k)
    for members in by_prefix.values():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if same_work(members[i], members[j]):
                    uf.union(members[i], members[j])

    blocks = defaultdict(list)
    for k in keys:
        blocks[("head", k[:block_len])].append(k)
        blocks[("tail", k[-block_len:])].append(k)
    for members in blocks.values():
        if len(members) < 2 or len(members) > 400:   # skip degenerate blocks
            continue
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                x, y = members[a], members[b]
                if uf.find(x) == uf.find(y):
                    continue
                if same_work(x, y):
                    uf.union(x, y)
    return uf


def main() -> None:
    # --- load and validate -------------------------------------------------
    try:
        export = pd.read_csv(SCOPUS_WITH_REFS, dtype=str).fillna("")
        sheet = pd.read_csv(SCREENING_SHEET, dtype=str).fillna("")
    except FileNotFoundError as exc:
        sys.exit(f"Could not open {exc.filename} — check the paths in CONFIG.")

    if "References" not in export.columns:
        sys.exit("The Scopus export has no 'References' column. Re-export with\n"
                 "'Include references' ticked — last item under 'Other information'.")
    if "EID" not in export.columns:
        sys.exit("The Scopus export has no 'EID' column.")

    missing = {COL_EID, COL_DECISION, COL_TITLE} - set(sheet.columns)
    if missing:
        sys.exit(f"Screening sheet is missing column(s): {sorted(missing)}\n"
                 f"Columns present: {sorted(sheet.columns)[:12]} ...")

    included = sheet[sheet[COL_DECISION].map(is_included)]
    print(f"screening sheet          : {len(sheet)} records")
    print(f"marked included          : {len(included)}")
    if included.empty:
        sys.exit("No records matched INCLUDE_PREFIXES — check the Decision column.")

    # readable id per included study, for the provenance column
    if COL_ID in sheet.columns:
        eid_to_id = dict(zip(sheet[COL_EID], sheet[COL_ID].astype(str).str.strip()))
    else:
        eid_to_id = {}

    export_by_eid = export.drop_duplicates("EID").set_index("EID")
    matched = [e for e in included[COL_EID] if e in export_by_eid.index]
    if len(matched) < len(included):
        print(f"WARNING: {len(included) - len(matched)} included records are not in "
              f"the export and are skipped.")
    print(f"matched into the export  : {len(matched)}")

    # --- split and parse ----------------------------------------------------
    instances = []
    for eid in matched:
        refs = str(export_by_eid.at[eid, "References"])
        if not refs.strip():
            continue
        for ref in REF_BOUNDARY.split(refs):
            if len(ref.strip()) < 15:
                continue
            authors, title, venue, year = parse_reference(ref)
            key = normalise(title)
            if len(key) < MIN_TITLE_CHARS:
                continue
            instances.append({"citing_eid": eid_to_id.get(eid, eid), "authors": authors,
                              "title": title, "venue": venue,
                              "year": year, "key": key})

    refs_df = pd.DataFrame(instances)
    print(f"reference instances      : {len(refs_df)}")

    # --- exact grouping, carrying the SET of citing studies -----------------
    works = (
        refs_df.groupby("key")
        .agg(citing=("citing_eid", lambda s: set(s)),
             title=("title", "first"),
             venue=("venue", "first"),
             year=("year", "first"),
             authors=("authors", "first"))
    )
    print(f"distinct works (exact)   : {len(works)}")

    # --- fuzzy clustering ---------------------------------------------------
    uf = fuzzy_clusters(list(works.index), FUZZY_THRESHOLD, BLOCK_LEN, PREFIX_LEN)
    merged = defaultdict(list)
    for k in works.index:
        merged[uf.find(k)].append(k)

    rows = []
    for root, members in merged.items():
        citing = set()
        for k in members:
            citing |= works.citing[k]          # UNION of citing studies,
        best = min(members, key=len)           # shortest = least venue bleed
        rows.append({
            "key": root,
            # which included studies cite this work — so any cited_by_n can be
            # traced back to the exact papers responsible
            "citing_studies": "; ".join(sorted(citing)),
            # cited_by_n is the number of UNIQUE included studies citing this
            # work. Summing the per-variant counts would double-count a study
            # that cites two spelling variants of the same reference.
            "cited_by_n": len(citing),
            "title": works.title[best],
            "venue": works.venue[best],
            "year": works.year[best],
            "authors": works.authors[best],
        })
    grouped = pd.DataFrame(rows)
    print(f"fuzzy variants merged    : {len(works) - len(grouped)}")
    print(f"distinct works (final)   : {len(grouped)}")

    # --- remove works already screened (exact, then fuzzy) ------------------
    screened_keys = {normalise(t) for t in sheet[COL_TITLE] if normalise(t)}
    exact_hit = grouped.key.isin(screened_keys)

    screened_blocks = defaultdict(list)
    for k in screened_keys:
        screened_blocks[k[:BLOCK_LEN]].append(k)
        screened_blocks[k[-BLOCK_LEN:]].append(k)

    # A reference title sometimes carries trailing venue text that the split
    # above did not catch. Comparing the leading PREFIX_LEN characters absorbs
    # that tail; 60 characters of exact agreement is not something two
    # different papers produce by accident.
    screened_by_prefix = defaultdict(list)
    for s in screened_keys:
        if len(s) >= PREFIX_LEN:
            screened_by_prefix[s[:PREFIX_LEN]].append(s)

    def fuzzy_seen(k):
        cands = set(screened_blocks.get(k[:BLOCK_LEN], []) +
                    screened_blocks.get(k[-BLOCK_LEN:], []))
        if len(k) >= PREFIX_LEN:
            cands |= set(screened_by_prefix.get(k[:PREFIX_LEN], []))
        return any(same_work(k, c) for c in cands)

    fuzzy_hit = pd.Series(
        [False if e else fuzzy_seen(k) for k, e in zip(grouped.key, exact_hit)],
        index=grouped.index,
    )
    print(f"already screened (exact) : {int(exact_hit.sum())}  removed")
    print(f"possibly already screened: {int(fuzzy_hit.sum())}  KEPT and flagged")

    # Only an EXACT normalised-title match is removed. A prefix or fuzzy match
    # is kept in the output and flagged instead.
    #
    # The two error modes are not symmetric. A duplicate left in the list costs
    # one glance. A candidate wrongly judged "already screened" disappears from
    # the review with no trace, and could be a study that belonged in it. So
    # the uncertain cases stay visible and the reviewer clears them.
    candidates = grouped[~exact_hit].copy()
    candidates["possibly_already_screened"] = fuzzy_hit[~exact_hit].map(
        lambda x: "CHECK - may duplicate a screened record" if x else ""
    )
    candidates = candidates.sort_values(["cited_by_n", "year"],
                                        ascending=[False, False]).reset_index(drop=True)
    candidates.insert(0, "SBID", [f"B{i:04d}" for i in range(1, len(candidates) + 1)])

    candidates["DECISION"] = ""      # intentionally empty: this script screens nothing
    candidates["CRITERION"] = ""
    candidates["NOTE"] = ""

    candidates[["SBID", "cited_by_n", "year", "authors", "title", "venue",
                "citing_studies", "possibly_already_screened",
                "DECISION", "CRITERION", "NOTE"]].to_csv(
        OUTPUT, index=False, quoting=csv.QUOTE_ALL)

    print()
    print(f"NEW CANDIDATES TO SCREEN : {len(candidates)}")
    print(f"   cited by 2 or more    : {int((candidates.cited_by_n >= 2).sum())}")
    print(f"   cited by 5 or more    : {int((candidates.cited_by_n >= 5).sum())}")
    print(f"   flagged to check      : {int((candidates.possibly_already_screened != '').sum())}")
    print(f"written to               : {OUTPUT}")
    print()
    print(f"parameters: FUZZY_THRESHOLD={FUZZY_THRESHOLD} BLOCK_LEN={BLOCK_LEN} "
          f"MIN_TITLE_CHARS={MIN_TITLE_CHARS} PREFIX_LEN={PREFIX_LEN}")


if __name__ == "__main__":
    main()
