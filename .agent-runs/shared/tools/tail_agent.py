import json,sys
f=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 25
rows=[json.loads(l) for l in open(f)]
out=[]
for r in rows:
    m=r.get('message') or {}
    c=m.get('content')
    if not isinstance(c,list): 
        if isinstance(c,str): out.append((r.get('type'),c[:600]))
        continue
    for x in c:
        t=x.get('type')
        if t=='text': out.append(('TEXT',x['text'][:1200]))
        elif t=='tool_use': out.append(('TOOL',json.dumps(x.get('input'),ensure_ascii=False)[:400]))
        elif t=='tool_result':
            cc=x.get('content'); s=cc if isinstance(cc,str) else json.dumps(cc,ensure_ascii=False)
            out.append(('RES',s[:300]))
for o in out[-n:]: print('--',o[0],o[1])
