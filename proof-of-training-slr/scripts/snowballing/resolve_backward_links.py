#!/usr/bin/env python3
"""
resolve_backward_links.py
=========================

PROBLEM
-------
BACKWARD-screened.csv was built by parsing the `References` field of the
Scopus export.  Scopus stores each cited reference as one plain text string
("Hartmann F., Federated Learning, (2018)") and does NOT attach an EID or a
DOI to it.  So unlike the forward candidates -- which came from a Scopus
export and therefore carried real identifiers -- the backward candidates had
no identifier to build a direct link from, and the file only carries title
SEARCH urls.

WHAT THIS SCRIPT DOES
---------------------
Looks each title up in two public bibliographic services and, when it finds
a confident match, writes a direct link to that paper's abstract page:

  1. Crossref  (api.crossref.org)  -- the DOI registry.  Covers IEEE, ACM,
     Springer, Elsevier, Wiley, and most journals/conferences.  Gives a DOI,
     so the link becomes https://doi.org/<DOI>.
  2. arXiv     (export.arxiv.org)  -- preprints only, used for the rows
     Crossref does not have.  Gives https://arxiv.org/abs/<id>.

A title lookup is a GUESS, so every guess is scored and recorded rather than
applied silently:

  * match accepted only when the returned title matches ours at >= 0.95
    similarity, using the SAME same_work() comparison as backward_snowball.py
    and forward_snowball.py.  All three scripts must agree about when two
    strings are the same work.
  * a returned year more than 1 year off ours downgrades the row to
    "uncertain" instead of accepting it.
  * near-misses in the 0.90-0.95 band are written to links_to_verify.csv for
    eyeball checking -- the same pattern as removals_to_verify.csv.
  * the original scholar_search / scopus_title_search columns are NEVER
    deleted.  An unresolved row is no worse off than it is today.

The run is RESUMABLE.  Every answer is cached to link_cache.json, so you can
Ctrl-C at row 1400 and restart without redoing the first 1400 lookups.

USAGE
-----
    python resolve_backward_links.py                  # all 2,649 rows
    python resolve_backward_links.py --priority-only   # only the rows you
                                                       # will actually open
    python resolve_backward_links.py --input MY-WORKING-COPY.csv

--priority-only resolves just the rows that are flagged review-first or
pre-screened include / include-borderline / exclude-borderline.  Under the
TITLE-ONLY RULE you screen the other ~2,250 from the title alone and never
open them, so resolving those is optional.  Start here if you want to begin
screening sooner; run the full pass later if you want it complete.

INPUT   BACKWARD-screened.csv   (or your working copy, via --input)
OUTPUT  BACKWARD-screened-linked.csv   same rows + 4 new columns
        links_to_verify.csv            near-misses to eyeball
        link_cache.json                resume cache (safe to delete)

Decisions you have already typed into the input file are preserved.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

# Identical to backward_snowball.py / forward_snowball.py.  Calibrated from
# four human verdicts on removals_to_verify.csv (0.91 was NOT a duplicate;
# 0.98 / 0.98 / 0.99 were).  All three scripts share this number on purpose.
FUZZY_THRESHOLD = 0.95

# Below this we do not even offer the match for inspection.
REVIEW_FLOOR = 0.90

# Shortest title we will try to resolve.  Same floor as the dedupe pass:
# "Federated Learning" style stubs match thousands of unrelated records.
MIN_TITLE_CHARS = 12

# A returned publication year further than this from the reference year means
# we probably matched a different paper (or a reprint).  Downgrade, not accept.
YEAR_TOLERANCE = 1

# Crossref asks that heavy users identify themselves; doing so puts you in
# their "polite pool", which is faster and more reliable than the anonymous
# pool.  Put your own address here.
# Crossref asks API users to identify themselves; set CONTACT_EMAIL in the environment.
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "anonymous@example.org")
USER_AGENT = f"SLR-snowball-linker/1.0 (mailto:{CONTACT_EMAIL})"

CROSSREF_DELAY = 0.15   # seconds between Crossref calls
ARXIV_DELAY    = 3.00   # arXiv's published policy is one call every 3 seconds
HTTP_TIMEOUT   = 30
MAX_RETRIES    = 3

CACHE_PATH = "link_cache.json"

# ---------------------------------------------------------------------------
# Title handling -- byte-identical logic to the other two scripts
# ---------------------------------------------------------------------------

def norm_title(t: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    t = t.lower().strip()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def same_work(a: str, b: str) -> bool:
    """True when two normalised titles denote the same work.

    Compared on equal-length truncations, so trailing venue text on one side
    cannot sink an otherwise identical title.  This is the same function the
    dedupe passes use; if it changes here it must change there too.
    """
    if a == b:
        return True
    n = min(len(a), len(b))
    if n < MIN_TITLE_CHARS:
        return False
    return SequenceMatcher(None, a[:n], b[:n]).ratio() >= FUZZY_THRESHOLD


def similarity(a: str, b: str) -> float:
    """The raw score behind same_work(), so we can record and band it."""
    if a == b:
        return 1.0
    n = min(len(a), len(b))
    if n < MIN_TITLE_CHARS:
        return 0.0
    return SequenceMatcher(None, a[:n], b[:n]).ratio()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class LookupFailed(Exception):
    """The service could not be reached at all.

    Kept separate from "the service answered and had nothing", because a dead
    network that silently reports no-match on all 2,649 rows would look like
    a finding about Crossref's coverage instead of a finding about the wifi.
    """


def http_get(url: str) -> bytes | None:
    """GET with retry and backoff.

    Returns bytes on success, None when the service answered but refused the
    request (4xx -- our query was bad), and raises LookupFailed when the
    service could not be reached at all.
    """
    last = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:                       # rate limited -- back off
                time.sleep(5 * (attempt + 1))
                continue
            if 400 <= e.code < 500:                 # our fault, do not retry
                return None
            last = f"HTTP {e.code}"
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            last = type(e).__name__
            time.sleep(2 * (attempt + 1))
    raise LookupFailed(last or "unreachable")


# ---------------------------------------------------------------------------
# Crossref
# ---------------------------------------------------------------------------

def crossref_lookup(title: str) -> dict | None:
    """Bibliographic title search.  Returns the best scoring candidate's
    DOI, title and year, or None."""
    q = urllib.parse.quote(title[:300])
    url = ("https://api.crossref.org/works"
           f"?query.bibliographic={q}&rows=3"
           "&select=DOI,title,issued,container-title,type")
    raw = http_get(url)          # may raise LookupFailed -- let it through
    if raw is None:
        return None
    try:
        items = json.loads(raw)["message"]["items"]
    except Exception:
        return None

    best = None
    for it in items:
        titles = it.get("title") or []
        if not titles:
            continue
        cand = norm_title(titles[0])
        score = similarity(norm_title(title), cand)
        if best is None or score > best["score"]:
            year = None
            parts = (it.get("issued") or {}).get("date-parts") or [[]]
            if parts and parts[0]:
                year = parts[0][0]
            venue = (it.get("container-title") or [""])[0]
            best = {"score": score, "doi": it.get("DOI", ""),
                    "title": titles[0], "year": year, "venue": venue,
                    "source": "crossref"}
    return best


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

ATOM = "{http://www.w3.org/2005/Atom}"

def arxiv_lookup(title: str) -> dict | None:
    """Title search against the arXiv API.  Used only for rows Crossref
    could not place -- many ML and cryptography papers in this set are
    preprints with no registered DOI."""
    clean = re.sub(r"[^A-Za-z0-9 ]+", " ", title)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) < MIN_TITLE_CHARS:
        return None
    q = urllib.parse.quote(f'ti:"{clean[:200]}"')
    url = f"http://export.arxiv.org/api/query?search_query={q}&max_results=3"
    raw = http_get(url)
    if raw is None:
        return None
    try:
        root = ET.fromstring(raw)
    except Exception:
        return None

    best = None
    for entry in root.findall(f"{ATOM}entry"):
        t_el = entry.find(f"{ATOM}title")
        id_el = entry.find(f"{ATOM}id")
        pub_el = entry.find(f"{ATOM}published")
        if t_el is None or id_el is None or not t_el.text:
            continue
        score = similarity(norm_title(title), norm_title(t_el.text))
        if best is None or score > best["score"]:
            year = None
            if pub_el is not None and pub_el.text:
                try:
                    year = int(pub_el.text[:4])
                except ValueError:
                    pass
            best = {"score": score, "arxiv_url": (id_el.text or "").strip(),
                    "title": t_el.text.strip(), "year": year,
                    "venue": "arXiv", "source": "arxiv"}
    return best


# ---------------------------------------------------------------------------
# Decide what to do with a candidate
# ---------------------------------------------------------------------------

def adjudicate(ref_title: str, ref_year: str, cand: dict | None) -> dict:
    """Turn a raw lookup result into a decision.

    Returns link, status, score, matched_title, matched_year.
    status is one of:
      resolved       match accepted, link is direct
      uncertain      plausible but not accepted -- see links_to_verify.csv
      year-mismatch  title matched but the year is wrong by > YEAR_TOLERANCE
      no-match       nothing close enough was returned
      not-attempted  title too short to look up safely
    """
    out = {"link": "", "status": "no-match", "score": "",
           "matched_title": "", "matched_year": "", "source": ""}
    if cand is None:
        return out

    score = cand["score"]
    out["score"] = f"{score:.3f}"
    out["matched_title"] = cand["title"]
    out["matched_year"] = str(cand["year"] or "")
    out["source"] = cand["source"]

    link = ""
    if cand["source"] == "crossref" and cand.get("doi"):
        link = "https://doi.org/" + cand["doi"]
    elif cand["source"] == "arxiv" and cand.get("arxiv_url"):
        link = cand["arxiv_url"].replace("http://", "https://")

    if not link:
        return out

    if score < REVIEW_FLOOR:
        out["status"] = "no-match"
        return out

    if score < FUZZY_THRESHOLD:
        out["link"] = link
        out["status"] = "uncertain"
        return out

    # Title is accepted.  Now cross-check the year as an independent signal.
    try:
        ry = int(str(ref_year).strip()[:4])
    except (ValueError, TypeError):
        ry = None
    cy = cand["year"]
    if ry and cy and abs(ry - cy) > YEAR_TOLERANCE:
        out["link"] = link
        out["status"] = "year-mismatch"
        return out

    out["link"] = link
    out["status"] = "resolved"
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="BACKWARD-screened.csv")
    ap.add_argument("--output", default="BACKWARD-screened-linked.csv")
    ap.add_argument("--priority-only", action="store_true",
                    help="resolve only review-first and pre-screened "
                         "include / include-borderline / exclude-borderline rows")
    ap.add_argument("--no-arxiv", action="store_true",
                    help="skip the arXiv fallback (much faster, fewer links)")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"ERROR: {args.input} not found. Run this in the folder "
                 f"that holds it.")

    with open(args.input, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("ERROR: input file has no rows.")

    for col in ("SBID", "title"):
        if col not in rows[0]:
            sys.exit(f"ERROR: input is missing the '{col}' column. You may be "
                     f"pointing at backward_candidates.csv instead of "
                     f"BACKWARD-screened.csv.")

    # Resume cache, keyed by SBID.
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as fh:
                cache = json.load(fh)
            print(f"resuming: {len(cache)} rows already looked up")
        except Exception:
            print("cache unreadable, starting fresh")
            cache = {}

    def in_priority(r: dict) -> bool:
        if (r.get("PRIORITY") or "").strip():
            return True
        d = (r.get("DECISION") or "").strip().lower()
        return d.startswith("include") or d == "exclude-borderline"

    targets = [r for r in rows if in_priority(r)] if args.priority_only else rows
    todo = [r for r in targets if r["SBID"] not in cache]

    print(f"rows in file              : {len(rows)}")
    print(f"rows in scope this run    : {len(targets)}"
          f"{'  (--priority-only)' if args.priority_only else ''}")
    print(f"already cached            : {len(targets) - len(todo)}")
    print(f"lookups to perform        : {len(todo)}")
    est = len(todo) * CROSSREF_DELAY + (0 if args.no_arxiv
                                        else len(todo) * 0.35 * ARXIV_DELAY)
    print(f"rough time estimate       : {est/60:.0f} min "
          f"(Ctrl-C is safe, progress is cached)\n")

    # --- connectivity pre-check -------------------------------------
    # Confirm Crossref answers for a title we KNOW it has before spending an
    # hour on lookups.  Without this, an offline run writes 2,649 rows of
    # "no-match" that look like a real result.
    if todo:
        print("checking that Crossref is reachable ...", end=" ", flush=True)
        try:
            probe = crossref_lookup("Attention Is All You Need")
        except LookupFailed as e:
            sys.exit(f"\nERROR: cannot reach api.crossref.org ({e}).\n"
                     f"Nothing was written. Check your connection, or a "
                     f"proxy/VPN/firewall blocking outbound HTTPS, and rerun.\n"
                     f"Your cached progress is safe in {CACHE_PATH}.")
        if probe is None or probe["score"] < REVIEW_FLOOR:
            sys.exit("\nERROR: Crossref answered but did not return the probe "
                     "paper. The API may have changed. Nothing was written.")
        print(f"ok (probe matched at {probe['score']:.3f})\n")

    stats = {"resolved": 0, "uncertain": 0, "year-mismatch": 0,
             "no-match": 0, "not-attempted": 0, "lookup-failed": 0}
    consecutive_failures = 0
    try:
        for i, r in enumerate(todo, 1):
            title = (r.get("title") or "").strip()
            year = (r.get("year") or "").strip()

            if len(norm_title(title)) < MIN_TITLE_CHARS:
                res = {"link": "", "status": "not-attempted", "score": "",
                       "matched_title": "", "matched_year": "", "source": ""}
            else:
                try:
                    cand = crossref_lookup(title)
                    time.sleep(CROSSREF_DELAY)
                    res = adjudicate(title, year, cand)
                    consecutive_failures = 0
                except LookupFailed:
                    res = {"link": "", "status": "lookup-failed", "score": "",
                           "matched_title": "", "matched_year": "", "source": ""}
                    consecutive_failures += 1
                    if consecutive_failures >= 10:
                        print(f"\nABORTING: 10 lookups in a row could not "
                              f"reach the service. This is a connection "
                              f"problem, not a coverage result.")
                        print(f"Cached progress is safe; rerun to continue "
                              f"from row {i}.")
                        break

                if res["status"] not in ("resolved", "lookup-failed") \
                        and not args.no_arxiv:
                    try:
                        acand = arxiv_lookup(title)
                        time.sleep(ARXIV_DELAY)
                        ares = adjudicate(title, year, acand)
                        rank = {"resolved": 3, "year-mismatch": 2,
                                "uncertain": 1, "no-match": 0,
                                "not-attempted": 0, "lookup-failed": 0}
                        if rank[ares["status"]] > rank[res["status"]]:
                            res = ares
                    except LookupFailed:
                        pass        # keep the Crossref verdict

            # A failure to reach the service is not an answer, so it is not
            # cached -- the next run retries it.  Every other outcome is.
            if res["status"] != "lookup-failed":
                cache[r["SBID"]] = res
            stats[res["status"]] = stats.get(res["status"], 0) + 1

            if i % 25 == 0 or i == len(todo):
                with open(CACHE_PATH, "w", encoding="utf-8") as fh:
                    json.dump(cache, fh)
                done = stats["resolved"]
                print(f"  {i}/{len(todo)}  resolved={done} "
                      f"uncertain={stats['uncertain']} "
                      f"year-mismatch={stats['year-mismatch']} "
                      f"no-match={stats['no-match']}")
    except KeyboardInterrupt:
        print("\ninterrupted -- writing what we have; rerun to continue")

    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)

    # ----- write the enriched file -------------------------------------
    new_cols = ["abstract_link", "link_status", "link_score", "matched_title"]
    fieldnames = list(rows[0].keys())
    # Insert the new columns just before the fallback search urls, so the
    # direct link is the first link you see on the row.
    anchor = fieldnames.index("scholar_search") if "scholar_search" in fieldnames \
             else len(fieldnames)
    fieldnames = fieldnames[:anchor] + new_cols + fieldnames[anchor:]

    verify = []
    for r in rows:
        res = cache.get(r["SBID"])
        if res is None:
            r["abstract_link"] = ""
            r["link_status"] = "not-run"
            r["link_score"] = ""
            r["matched_title"] = ""
        else:
            r["abstract_link"] = res["link"]
            r["link_status"] = res["status"]
            r["link_score"] = res["score"]
            r["matched_title"] = res["matched_title"]
            if res["status"] in ("uncertain", "year-mismatch"):
                verify.append({
                    "SBID": r["SBID"],
                    "link_status": res["status"],
                    "link_score": res["score"],
                    "our_title": r.get("title", ""),
                    "our_year": r.get("year", ""),
                    "matched_title": res["matched_title"],
                    "matched_year": res["matched_year"],
                    "source": res["source"],
                    "abstract_link": res["link"],
                })

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    if verify:
        with open("links_to_verify.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(verify[0].keys()),
                               quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(verify)

    # ----- report ------------------------------------------------------
    counted = [cache[r["SBID"]] for r in rows if r["SBID"] in cache]
    tally = {}
    for res in counted:
        tally[res["status"]] = tally.get(res["status"], 0) + 1
    by_src = {}
    for res in counted:
        if res["status"] == "resolved":
            by_src[res["source"]] = by_src.get(res["source"], 0) + 1

    print("\n" + "=" * 62)
    print("PARAMETERS")
    print(f"  FUZZY_THRESHOLD   {FUZZY_THRESHOLD}   (accept a title match)")
    print(f"  REVIEW_FLOOR      {REVIEW_FLOOR}   (offer for inspection)")
    print(f"  YEAR_TOLERANCE    {YEAR_TOLERANCE}    years")
    print(f"  MIN_TITLE_CHARS   {MIN_TITLE_CHARS}")
    print("\nRESULTS")
    print(f"  rows looked up            : {len(counted)}")
    for k in ("resolved", "uncertain", "year-mismatch", "no-match",
              "not-attempted", "lookup-failed"):
        if k in tally:
            print(f"    {k:<22}: {tally[k]}")
    for src, n in sorted(by_src.items()):
        print(f"      via {src:<18}: {n}")
    print(f"\n  wrote {args.output}")
    if verify:
        print(f"  wrote links_to_verify.csv  ({len(verify)} rows to eyeball)")
    unrun = sum(1 for r in rows if r["SBID"] not in cache)
    if unrun and not args.priority_only:
        print(f"\n  {unrun} rows still have no answer -- rerun to finish them.")
    elif unrun:
        print(f"\n  {unrun} rows outside the priority band were not looked up.")
        print("  Drop --priority-only to do the rest.")
    print("\nNOTE  'resolved' links are title matches, not Scopus records.")
    print("      The original scholar_search and scopus_title_search columns")
    print("      are untouched -- use them for any row without a link.")
    print("=" * 62)


if __name__ == "__main__":
    main()
