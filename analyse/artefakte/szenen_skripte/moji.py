import lib
bp = lib.bypage()
best = []
for pk, rs in bp.items():
    prev = ''
    for r in rs:
        add = lib.added(prev, r['body']); prev = r['body']
        for l in add:
            n = l.count('Ã') + l.count('Â')
            if n >= 4: best.append((n, r['time'], r['label'], pk, r['_line']))
best.sort(reverse=True)
for b in best[:15]: print(b)
print('lines:', len(best))
