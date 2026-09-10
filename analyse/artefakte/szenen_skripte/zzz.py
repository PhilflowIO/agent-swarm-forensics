import lib
ev = lib.load('events.jsonl')
d = [e for e in ev if e['event_type'] == 'delete' and e['time'][:10] == '2026-06-19']
print('deletions on 19 Jun:', len(d))
d.sort(key=lambda e: e['time'])
print('first', d[0]['time'], d[0]['page'], ' last', d[-1]['time'], d[-1]['page'])
for e in d:
    if e['page'] in ('DataUSAConstructionWageSep18Live', 'ZZZDataUSAConstructionWageLive'): print('  >>', e['time'], e['page'])
# what was being deleted at 15:40-15:50
for e in d:
    if '15:4' in e['time']: print('   ', e['time'], e['page'])
