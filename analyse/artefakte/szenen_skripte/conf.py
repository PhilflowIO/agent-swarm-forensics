import lib, re
from collections import Counter
bp = lib.bypage()
pat = re.compile(r"overwrote|overwrit|clobber|edit conflict|lost my edit|please do not overwrite|section-edit|append only|do not delete|someone deleted|was deleted|restored|whoever deleted|apolog", re.I)
cnt = Counter(); rec = {}
for pk, rs in bp.items():
    prev = ''
    for r in rs:
        add = lib.added(prev, r['body']); prev = r['body']
        for l in add:
            k = l.strip()
            if len(k) < 50: continue
            if pat.search(k):
                cnt[k] += 1; rec.setdefault(k, (r['time'], r['label'], pk, r['_line']))
u = [k for k, v in cnt.items() if v == 1]
print(len(cnt), len(u))
with open(__import__('os').path.dirname(__file__) + '/sc14.txt', 'w') as f:
    for k in sorted(u, key=lambda x: rec[x][0]):
        t, lab, pk, ln = rec[k]
        f.write('%s | %s | %s | L%s\n   %s\n' % (t, lab, pk, ln, k[:420]))
