import lib
bp = lib.bypage()
for r, add in lib.page_deltas('dse~DataUSALanguageR5LiveDec29', bp):
    for l in add:
        if 'URGENT CORRECTION' in l:
            print('seq%d %s %s L%d len=%d' % (r['seq'], r['time'], r['label'], r['_line'], len(l)))
            print('   ', l[:230])
            print('   ...', l[-120:])
