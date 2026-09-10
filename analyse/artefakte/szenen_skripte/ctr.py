import lib, re
from collections import Counter
bp = lib.bypage()
first = {}; per_day = Counter(); labels=set(); ns=Counter()
for pk, rs in bp.items():
    prev = ''
    for r in rs:
        add = lib.added(prev, r['body']); prev = r['body']
        for l in add:
            if 'counterapi' in l.lower():
                per_day[r['time'][:10]] += 1; labels.add(r['label'])
                for m in re.finditer(r'counterapi\.dev/v1/([A-Za-z0-9_-]+)', l): ns[m.group(1)] += 1
                first.setdefault('x', (r['time'], r['label'], pk, r['_line'], l[:300]))
print(first['x'])
print(sorted(per_day.items()))
print('labels:', len(labels))
print(len(ns), ns.most_common(3))
