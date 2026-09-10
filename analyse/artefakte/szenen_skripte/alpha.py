import lib
ev = lib.load('events.jsonl')
d = sorted([e for e in ev if e['event_type'] == 'delete' and e['time'][:10] == '2026-06-19'], key=lambda e: e['time'])
run = 1; runs = []
for i in range(1, len(d)):
    if d[i]['page'].lower() >= d[i-1]['page'].lower(): run += 1
    else:
        runs.append((run, d[i-1]['time'], d[i-1]['page'], d[i]['time'], d[i]['page'])); run = 1
runs.append((run, d[-1]['time'], d[-1]['page'], '', ''))
runs.sort(reverse=True)
for r in runs[:6]: print(r)
