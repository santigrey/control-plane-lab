import sys
R='/home/jes/control-plane/orchestrator/ai_operator/tools/registry.py'
H='/home/jes/control-plane/docs/phase1_handlers.py'
G='/home/jes/control-plane/docs/phase1_regs.py'
with open(R) as f: src=f.read()
if '_check_jail' in src:
    print('ABORT: already merged'); sys.exit(1)
with open(H) as f: handlers=f.read()
with open(G) as f: regs=f.read()
# strip the _telegram_rate line from handlers (insert separately)
hnd_body=handlers.split('_telegram_rate = []\n',1)[1]
# 1) insert _telegram_rate after chains import
a='from ai_operator.tools.chains import CHAIN_TEMPLATES\n'
i=src.index(a)+len(a)
src=src[:i]+'\n_telegram_rate = []\n'+src[i:]
# 2) insert handlers before default_registry
b='def default_registry()'
j=src.index(b)
src=src[:j]+hnd_body+'\n\n'+src[j:]
# 3) insert regs before return r
k=src.rindex('    return r')
src=src[:k]+'\n'+regs+'\n\n'+src[k:]
with open(R,'w') as f: f.write(src)
print('MERGE COMPLETE')
