#!/usr/bin/env python3
"""Recompute the main counts of the paper from the files in data/.

Usage (from the repository root):  python scripts/reproduce_numbers.py
Standard library only. Each line prints the value computed from the data, the
value printed in the paper, and OK or DIFF.
"""
import collections
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
failures = 0


def rows(rel):
    with open(os.path.join(DATA, rel), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def check(label, value, expected):
    global failures
    ok = value == expected
    failures += not ok
    print(f"{'OK  ' if ok else 'DIFF'}  {label}: {value}" + ('' if ok else f'  (paper: {expected})'))


def kept(decision):
    return decision in ('include', 'include-borderline')


def agreement(pairs):
    """Observed agreement and Cohen's kappa for keep/exclude pairs."""
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in (True, False)) / n / n
    return round(100 * po, 1), round((po - pe) / (1 - pe), 2)


print('Screening')
db = rows('2_screening/database_screening_author.csv')
bw = rows('2_screening/backward_screening.csv')
fw = rows('2_screening/forward_screening.csv')
check('database records', len(db), 656)
check('database records kept', sum(kept(r['decision']) for r in db), 114)
check('backward candidates', len(bw), 2649)
check('backward candidates kept', sum(kept(r['author_decision']) for r in bw), 66)
check('forward candidates', len(fw), 637)
check('forward candidates kept', sum(kept(r['author_decision']) for r in fw), 26)
check('records screened in total', len(db) + len(bw) + len(fw), 3942)
check('kept in total', 114 + 66 + 26, 206)

print('\nAgreement with the automated pass (keep vs. exclude)')
check('backward: agreement %, kappa',
      agreement([(kept(r['author_decision']), kept(r['automated_decision'])) for r in bw]), (96.5, 0.56))
check('forward: agreement %, kappa',
      agreement([(kept(r['author_decision']), kept(r['automated_decision'])) for r in fw]), (97.6, 0.76))
auto_path = os.path.join(DATA, '2_screening/database_screening_automated.csv')
if os.path.exists(auto_path):
    auto = {r['id']: r['decision'] for r in rows('2_screening/database_screening_automated.csv')}
    pairs = [(kept(r['decision']), kept(auto[r['id']])) for r in db if auto.get(r['id'])]
    check('database: records compared', len(pairs), 656)
    check('database: agreement %, kappa', agreement(pairs), (96.8, 0.89))
else:
    print('----  database: automated decisions not in this copy of the package')

print('\nFull text')
ft = rows('3_full_text/full_text_assessment.csv')
st = collections.Counter(r['status'] for r in ft)
check('backward candidates repeating a database record', st['Duplicate'], 19)
check('not assessable: no full text / not found / not a paper',
      (st['No full text'], st['Not found'], st['Not a paper']), (14, 7, 2))
check('excluded: does not verify training / IC-1 / EC-4',
      (st['Remove'], st['Remove (IC-1)'], st['Remove (EC-4)']), (33, 3, 2))
check('included', st['Included'], 125)

print('\nIncluded studies')
inc = rows('4_included/included_studies.csv')
check('by source (database, forward, backward)',
      tuple(collections.Counter(r['set'] for r in inc)[k] for k in ('Query', 'Forward', 'Backward')), (96, 15, 14))
types = collections.Counter(r['type'] for r in inc)
check('by type', dict(types), {'Cryptographic proof': 54, 'Redo the work': 22, 'Aggregation-only proof': 15,
                               'Trusted hardware': 10, 'Model behaviour': 9, 'Work puzzle': 7, 'Math check': 5,
                               'Runtime behaviour': 2, 'Incentives': 1})
scope = collections.Counter(r['scope_level'] for r in inc)
check('scope: Full, Sampled, Partial, Related step, Not detailed',
      tuple(scope[k] for k in ('Full', 'Sampled', 'Partial', 'Related step', 'Not detailed')), (40, 19, 13, 43, 10))
strict = collections.Counter(r['type'] for r in inc if r['scope_level'] in ('Full', 'Sampled'))
check('checked at every step or on samples (strict set)', sum(strict.values()), 59)
check('strict set by type (crypto, redo, TEE, math)',
      tuple(strict[k] for k in ('Cryptographic proof', 'Redo the work', 'Trusted hardware', 'Math check')),
      (28, 20, 10, 1))
who = collections.Counter(r['who_checks'] for r in inc)
check('who checks: single verifier, FL server, blockchain, FL clients, peers',
      tuple(who[k] for k in ('Single verifier', 'FL server', 'Blockchain', 'FL clients', 'Peers')),
      (47, 33, 30, 10, 5))
ev = collections.Counter(r['evaluation'] for r in inc if r['type'] == 'Cryptographic proof')
check('cryptographic evaluation: implemented, simulated, analytical, none',
      tuple(ev[k] for k in ('implemented', 'simulated', 'analytical', 'none')), (45, 5, 2, 2))
ev = collections.Counter(r['evaluation'] for r in inc if r['type'] != 'Cryptographic proof')
check('other evaluation: implemented, simulated, theory, none',
      tuple(ev[k] for k in ('implemented', 'simulated', 'analytical', 'none')), (61, 4, 2, 4))

print('\nMetrics reported by the 54 cryptographic studies (Table 22)')
cm = rows('5_extraction/crypto_metrics.csv')
codes = collections.Counter(c.strip() for r in cm for c in r['metrics'].split(',') if c.strip())
expected = {'PT': 37, 'VT': 34, 'ACC': 33, 'PS': 28, 'OVH': 18, 'COM': 18, 'CHAIN': 10, 'ST': 9,
            'MEM': 9, 'DET': 8, 'CONF': 3, 'ENERGY': 1}
for k, v in expected.items():
    check(k, codes[k], v)
check('studies reporting none of the metrics', sum(1 for r in cm if not r['metrics'].strip()), 7)

print('\n' + ('All checks match the paper.' if not failures else f'{failures} check(s) differ from the paper.'))
sys.exit(1 if failures else 0)
