import lib, re
bp = lib.bypage()
pad = set(); raw_before = set()
for pk, rs in bp.items():
    prev = ''
    for r in rs:
        add = lib.added(prev, r['body']); prev = r['body']
        for l in add:
            if r['time'] < '2026-06-20T05:03:37Z':
                if re.search(r'9\.70|16\.40|14\.60', l): pad.add(r['label'])
                if re.search(r'\b9\.69|16\.38|14\.59', l): raw_before.add(r['label'])
print('labels using padded values before Dec30 proof:', len(pad))
print('labels using raw values before proof:', len(raw_before), sorted(raw_before))
