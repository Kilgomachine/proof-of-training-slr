#!/usr/bin/env python3
"""
Verify that forward snowballing covered every included study.

Three checks:
  A  BLOCK COVERAGE     do the EID query blocks cover all included studies
                        exactly once, with no gaps and no overlaps?
  B  EXPORT COVERAGE    did every block's cited-by export arrive, and does
                        the merged file account for all of them?
  C  CITATION RECOVERY  for each seed, Scopus reports N citations. How many
                        citing papers did we actually capture that reference
                        it? A seed with many citations and none recovered
                        means its block was missed or mis-exported.

Check C will always undercount: a citing paper is only credited to a seed when
the seed's title can be found in that paper's reference list, and reference
formatting defeats the parser some of the time. Look for ZEROES on seeds with
high citation counts, not for exact agreement.
"""
import re, sys, glob
from collections import defaultdict
import pandas as pd

SCREENING_SHEET = "screening_sheet.csv"
BLOCKS_FILE     = "forward-eid-blocks.txt"
BLOCK_EXPORTS   = "cited_by_block*.csv"
MERGED          = "cited_by_export.csv"
COL_DECISION, COL_EID, COL_TITLE, COL_ID = "Decision", "EID", "Title", "ID"
MIN_TITLE_CHARS, PREFIX_LEN = 12, 60

norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s).lower())).strip()
REF_BOUNDARY = re.compile(r"(?<=\(\d{4}\))\s*;\s*")
VENUE_START = re.compile(r",\s*(?:pp?\.|\d+\s*(?:,|$)|\(\d{4}\)|(?:Proceedings|Journal|IEEE|ACM|Advances|Lecture\s+Notes|Conference|Transactions|Int\.|Proc\.|arXiv|CoRR|In)\b)")

def ref_titles(refs):
    for ref in REF_BOUNDARY.split(str(refs)):
        if len(ref.strip()) < 15: continue
        y = re.search(r"\((\d{4})\)\s*$", ref.strip())
        body = ref[: y.start()].rstrip(" ,") if y else ref
        c = body.find(",")
        if c == -1: continue
        rest = body[c+1:].strip()
        m = VENUE_START.search(rest)
        k = norm((rest[: m.start()] if m else rest).strip().rstrip(","))
        if len(k) >= MIN_TITLE_CHARS: yield k

sheet = pd.read_csv(SCREENING_SHEET, dtype=str).fillna("")
inc = sheet[sheet[COL_DECISION].str.strip().str.lower().str.startswith(("include","imclude"))]
seed_eids = set(inc[COL_EID])
print(f"included studies in the screening sheet : {len(inc)}\n")

# ---- A ----------------------------------------------------------------
print("A. BLOCK COVERAGE")
txt = open(BLOCKS_FILE).read()
blocks = re.findall(r"-----\s*BLOCK (\d+) of \d+\s*\((\d+) papers\)\s*-----\n(.+?)\n", txt)
seen, dupes = set(), []
for n, cnt, q in blocks:
    ids = re.findall(r"EID\((2-s2\.0-\d+)\)", q)
    dupes += [i for i in ids if i in seen]
    seen |= set(ids)
    print(f"   block {n}: {len(ids)} EIDs declared {cnt}  all are seeds: {set(ids) <= seed_eids}")
missing = seed_eids - seen
print(f"   union of blocks            : {len(seen)}")
print(f"   seeds NOT in any block     : {len(missing)} {sorted(missing) if missing else ''}")
print(f"   EIDs in more than one block: {len(dupes)} {dupes if dupes else ''}")
print(f"   VERDICT: {'PASS' if not missing and not dupes and seen == seed_eids else 'FAIL'}\n")

# ---- B ----------------------------------------------------------------
print("B. EXPORT COVERAGE")
files = sorted(glob.glob(BLOCK_EXPORTS))
frames, total = [], 0
for f in files:
    d = pd.read_csv(f, dtype=str).fillna("")
    frames.append(d); total += len(d)
    print(f"   {f}: {len(d)} rows  refs {(d.get('References','').astype(str).str.strip()!='').sum()}"
          f"  abstracts {(d.get('Abstract','').astype(str).str.strip()!='').sum()}")
print(f"   block exports found        : {len(files)} (expected {len(blocks)})")
allrows = pd.concat(frames, ignore_index=True)
merged = pd.read_csv(MERGED, dtype=str).fillna("")
print(f"   rows across blocks         : {total}")
print(f"   unique EIDs across blocks  : {allrows.EID.nunique()}")
print(f"   rows in merged file        : {len(merged)}")
ok_b = len(files) == len(blocks) and allrows.EID.nunique() == len(merged)
print(f"   VERDICT: {'PASS' if ok_b else 'FAIL'}\n")

# ---- C ----------------------------------------------------------------
print("C. CITATION RECOVERY (per seed)")
seed_key = {}
for _, r in inc.iterrows():
    k = norm(r[COL_TITLE])
    if len(k) >= MIN_TITLE_CHARS:
        seed_key[k] = str(r.get(COL_ID, r[COL_EID])).strip()
by_prefix = defaultdict(list)
for k in seed_key:
    if len(k) >= PREFIX_LEN: by_prefix[k[:PREFIX_LEN]].append(k)

recovered = defaultdict(int)
for _, row in merged.iterrows():
    hits = set()
    for rk in ref_titles(row.get("References", "")):
        if rk in seed_key: hits.add(seed_key[rk])
        elif len(rk) >= PREFIX_LEN:
            for c in by_prefix.get(rk[:PREFIX_LEN], []): hits.add(seed_key[c])
    for h in hits: recovered[h] += 1

inc = inc.copy()
inc["scopus_cites"] = pd.to_numeric(inc["Cited by"], errors="coerce").fillna(0).astype(int)
inc["pid"] = inc[COL_ID].astype(str).str.strip()
inc["recovered"] = inc.pid.map(lambda p: recovered.get(p, 0))
cited = inc[inc.scopus_cites > 0]
print(f"   seeds with 0 citations in Scopus  : {(inc.scopus_cites==0).sum()}  (nothing to recover)")
print(f"   seeds with citations              : {len(cited)}")
print(f"   of those, recovered >=1 citer     : {(cited.recovered>0).sum()}")
zero = cited[cited.recovered==0].sort_values("scopus_cites", ascending=False)
print(f"   of those, recovered NOTHING       : {len(zero)}   <-- investigate these")
for _, r in zero.head(12).iterrows():
    print(f"        {r.pid}  scopus says {r.scopus_cites:>3} citations, recovered 0   {r[COL_TITLE][:52]}")
big = cited[(cited.scopus_cites>=10)]
print(f"\n   seeds with >=10 citations         : {len(big)}")
print(f"   of those, recovered >=1           : {(big.recovered>0).sum()}")
print(f"\n   VERDICT: {'PASS' if len(zero)==0 else 'REVIEW — see the list above'}")
