# Scripts

Python 3. The three snowballing scripts (`backward_snowball.py`, `forward_snowball.py`, `verify_forward_coverage.py`) need pandas; the others use the standard library only. Run each script from a folder that holds its input files.

| Script | Inputs | Output | Purpose |
|---|---|---|---|
| `reproduce_numbers.py` | `data/` of this repository | printed report | Recomputes the main counts of the paper from the data files and compares each with the paper |
| `snowballing/backward_snowball.py` | `export_with_references.csv` (Scopus export of the 656 records, with references), `screening_sheet.csv` (the database screening decisions) | `backward_candidates.csv` | Splits the kept records' reference lists, parses each reference, merges duplicates (normalised titles, then `difflib` ratio ≥ 0.95 with union-find), removes works already screened, and lists the candidates with empty decision columns |
| `snowballing/forward_snowball.py` | `cited_by_export.csv` (Scopus cited-by export of the seeds, with references), `screening_sheet.csv`, `backward_candidates.csv` | `forward_candidates.csv` | Removes seeds, records already screened and backward candidates, and recovers which seed each citing paper cites from its own reference list |
| `snowballing/verify_forward_coverage.py` | `screening_sheet.csv`, `forward-eid-blocks.txt`, `cited_by_block*.csv`, `cited_by_export.csv` | printed report | Checks that the EID blocks cover every seed once, that every block's export arrived, and how many citations were recovered per seed |
| `snowballing/resolve_backward_links.py` | `BACKWARD-screened.csv` (backward candidates with decisions) | `BACKWARD-screened-linked.csv`, `links_to_verify.csv` | Looks up backward candidates in Crossref and arXiv to add direct links for full-text retrieval. Set `CONTACT_EMAIL` in the environment, as Crossref asks API users to identify themselves |
| `screening/build_q123_sheet.py` | `screening_sheet.csv`, `FORWARD-screened.csv`, `cited_by_export.csv`, `three-questions-answers.csv` | `Q123-blank.csv`, `Q123-firstpass.csv` | Builds the sheets for the three-question cross-check |

The file names in the Inputs column are the working names the scripts expect. `screening_sheet.csv` corresponds to the decisions in `data/2_screening/database_screening_author.csv` joined to the Scopus export; the Scopus exports themselves are not redistributed (see the main README).

The snowballing scripts make no inclusion decisions: every candidate they list was screened by hand.
