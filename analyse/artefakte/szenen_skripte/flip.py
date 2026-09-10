import lib, re
bp = lib.bypage()
before = set(); after = set(); rows = []
for pk, rs in bp.items():
    prev = ''
    for r in rs:
        add = lib.added(prev, r['body']); prev = r['body']
        for l in add:
            if re.search(r'16\.38|14\.59|\b9\.69|\b9\.91\b|23\.13', l) and r['time'] >= '2026-06-20T04':
                after.add(r['label']); rows.append((r['time'], r['label'], pk, r['_line']))
print('labels writing raw-values after 04:00 on 20 Jun:', len(after))
rows.sort()
print('first', rows[0], 'last', rows[-1], 'n', len(rows))
# who explicitly says they will switch
pat = re.compile(r'(will answer|now plan|plan to answer|choose|strongly plan|will use|switch)\D{0,25}(16\.38|14\.59|9\.69|23\.13)', re.I)
n = 0
for pk, rs in bp.items():
    prev = ''
    for r in rs:
        add = lib.added(prev, r['body']); prev = r['body']
        for l in add:
            if pat.search(l):
                n += 1; print('  ', r['time'], r['label'], pk, 'L%d' % r['_line'], '|', l[:170])
print('explicit switch statements:', n)
