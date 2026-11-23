#!/usr/bin/env python3
"""
build_q123_sheet.py
===================

Builds the review sheet for the supervisor's three questions:

  Q1  Does the mechanism concern TRAINING, rather than only inference,
      testing, deployment or another lifecycle stage?
  Q2  Is the setting DISTRIBUTED across multiple independent participants,
      clients, workers or nodes?
  Q3  Is there verifiable or measurable EVIDENCE that the participating
      client(s) actually performed the claimed training?

It produces two files with IDENTICAL row order and identical ROW numbers, so
they can be opened side by side and compared line for line:

  Q123-blank.csv       Q1/Q2/Q3/NOTE empty, for you to fill in
  Q123-firstpass.csv   the machine first pass, for reference

ROW ORDER
  1 .. 114    QUERY-INCLUDED   the studies retained from the database search
  115 .. 656  QUERY-EXCLUDED   the rest of the 656
  657 ..1293  FORWARD          the forward snowballing candidates

Delete the QUERY-EXCLUDED block if the supervisor only wants the included set;
the ROW numbers are assigned before any filtering so the two files stay aligned
either way.

INPUTS, all in this folder
  screening_sheet.csv          the 656 with your decisions
  FORWARD-screened.csv         the 637 forward candidates
  cited_by_export.csv          source of abstracts for the forward set
  three-questions-answers.csv  the first pass (only needed for the filled file)

USAGE
  python build_q123_sheet.py
"""

import csv
import os
import re
import sys

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

SCREENING = "screening_sheet.csv"
FORWARD   = "FORWARD-screened.csv"
CITEDBY   = "cited_by_export.csv"
FIRSTPASS = "three-questions-answers.csv"

ABSTRACT_CHARS = 700          # enough to decide most rows without opening the paper
INCLUDE_PREFIXES = ("include", "imclude", "inlcude", "includ")


def is_included(v):
    return str(v).strip().lower().startswith(INCLUDE_PREFIXES)


def scopus_url(eid):
    """Scopus record URL, built from the numeric tail of the EID.
    This is the same link format carried in the exports we have been using."""
    m = re.search(r"(\d+)$", str(eid).strip())
    return f"https://www.scopus.com/pages/publications/{m.group(1)}?origin=resultslist" if m else ""


def doi_url(doi):
    d = str(doi).strip()
    return f"https://doi.org/{d}" if d else ""


def clip(text, n):
    t = re.sub(r"\s+", " ", str(text)).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " ..."


def main():
    for f in (SCREENING, FORWARD):
        if not os.path.exists(f):
            sys.exit(f"ERROR: {f} not found. Run this in the folder holding the inputs.")

    with open(SCREENING, newline="", encoding="utf-8-sig") as fh:
        query = list(csv.DictReader(fh))
    with open(FORWARD, newline="", encoding="utf-8-sig") as fh:
        fwd = list(csv.DictReader(fh))

    abstracts = {}
    if os.path.exists(CITEDBY):
        with open(CITEDBY, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                abstracts[r.get("EID", "").strip()] = r.get("Abstract", "")
    else:
        print(f"NOTE: {CITEDBY} not found - the forward rows will have no abstract.")

    rows = []

    # ---- the 656, included first so they sit at the top ------------------
    inc = [r for r in query if is_included(r.get("Decision"))]
    exc = [r for r in query if not is_included(r.get("Decision"))]
    print(f"query records      : {len(query)}  ({len(inc)} included, {len(exc)} excluded)")

    for group, label in ((inc, "QUERY-INCLUDED"), (exc, "QUERY-EXCLUDED")):
        for r in group:
            eid = r.get("EID", "").strip()
            rows.append({
                "SET": label,
                "ID": (r.get("ID") or eid).strip(),
                "YEAR": r.get("Year", ""),
                "TITLE": r.get("Title", ""),
                "VENUE": r.get("Source title", ""),
                "SCOPUS_LINK": r.get("Link", "").strip() or scopus_url(eid),
                "DOI_LINK": doi_url(r.get("DOI", "")),
                "PRIOR_DECISION": (r.get("Decision") or "").strip(),
                "PRIOR_CRITERION": (r.get("criteria1(EC/IC)") or "").strip(),
                "ABSTRACT": clip(r.get("Abstract", ""), ABSTRACT_CHARS),
            })

    # ---- the forward candidates, underneath ------------------------------
    print(f"forward candidates : {len(fwd)}")
    for r in fwd:
        eid = r.get("eid", "").strip()
        rows.append({
            "SET": "FORWARD",
            "ID": r.get("SBID", "").strip(),
            "YEAR": r.get("year", ""),
            "TITLE": r.get("title", ""),
            "VENUE": r.get("venue", ""),
            "SCOPUS_LINK": r.get("scopus_link", "").strip() or scopus_url(eid),
            "DOI_LINK": r.get("doi_link", "").strip() or doi_url(r.get("doi", "")),
            "PRIOR_DECISION": (r.get("DECISION") or "").strip(),
            "PRIOR_CRITERION": (r.get("CRITERION") or "").strip(),
            "ABSTRACT": clip(abstracts.get(eid, ""), ABSTRACT_CHARS),
        })

    # ROW is assigned once, before anything is filtered, so the blank file and
    # the first-pass file stay aligned even if rows are deleted from one of them.
    for n, r in enumerate(rows, 1):
        r["ROW"] = n

    missing_link = sum(1 for r in rows if not r["SCOPUS_LINK"])
    missing_abs = sum(1 for r in rows if not r["ABSTRACT"])
    dupes = len(rows) - len({r["ID"] for r in rows})
    print(f"\ntotal rows         : {len(rows)}")
    print(f"  duplicate ids    : {dupes}")
    print(f"  missing links    : {missing_link}")
    print(f"  missing abstracts: {missing_abs}")
    if dupes:
        sys.exit("ERROR: duplicate ids - stopping rather than writing a sheet you cannot trust.")

    BASE = ["ROW", "SET", "ID", "YEAR", "TITLE", "VENUE",
            "SCOPUS_LINK", "DOI_LINK", "PRIOR_DECISION", "PRIOR_CRITERION", "ABSTRACT"]

    # ---- blank sheet -----------------------------------------------------
    cols = BASE + ["Q1_training", "Q2_distributed", "Q3_evidence", "NOTE"]
    with open("Q123-blank.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            w.writerow({**{c: r.get(c, "") for c in BASE},
                        "Q1_training": "", "Q2_distributed": "", "Q3_evidence": "", "NOTE": ""})
    print("wrote Q123-blank.csv")

    # ---- first-pass sheet, same order ------------------------------------
    if not os.path.exists(FIRSTPASS):
        print(f"NOTE: {FIRSTPASS} not found - skipping the first-pass file.")
        return
    with open(FIRSTPASS, newline="", encoding="utf-8-sig") as fh:
        fp = {r["ID"]: r for r in csv.DictReader(fh)}
    hit = sum(1 for r in rows if r["ID"] in fp)
    print(f"first-pass answers matched: {hit}/{len(rows)}")

    # REVIEW columns are present once the recheck has been run on the first pass.
    REVIEW = ["BLIND_PASS", "CONTESTED", "REVISED", "REVISION_REASON"]
    cols2 = BASE + ["Q1_training", "Q2_distributed", "Q3_evidence",
                    "PATTERN", "CONFIDENCE", "FLAGS", "NOTE"] + REVIEW
    with open("Q123-firstpass.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols2, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            a = fp.get(r["ID"], {})
            w.writerow({**{c: r.get(c, "") for c in BASE},
                        "Q1_training": a.get("Q1_training", ""),
                        "Q2_distributed": a.get("Q2_distributed", ""),
                        "Q3_evidence": a.get("Q3_evidence", ""),
                        "PATTERN": a.get("PATTERN", ""),
                        "CONFIDENCE": a.get("CONFIDENCE", ""),
                        "FLAGS": a.get("FLAGS", ""),
                        "NOTE": a.get("NOTE", ""),
                        **{c: a.get(c, "") for c in REVIEW}})
    print("wrote Q123-firstpass.csv")


if __name__ == "__main__":
    main()
