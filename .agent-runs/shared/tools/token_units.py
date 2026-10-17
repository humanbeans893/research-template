"""Sum token usage from Claude Code transcripts (deduplicated per message id).

units = input + 1.25*cache_creation + 0.1*cache_read + 5*output  (input-token equivalents)
usage: token_units.py <jsonl>... ; prints per file and the total; --since ISO limits entries.
"""
import json, sys, collections
args = sys.argv[1:]
since = None
if args and args[0] == '--since':
    since = args[1]; args = args[2:]
grand = collections.Counter()
for f in args:
    tot = collections.Counter(); seen = set()
    for line in open(f):
        r = json.loads(line)
        if since and (r.get('timestamp') or '') < since:
            continue
        m = r.get('message') or {}
        u = m.get('usage'); mid = m.get('id')
        if not u or mid in seen:
            continue
        seen.add(mid)
        for k in ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'):
            tot[k] += u.get(k) or 0
    units = tot['input_tokens'] + 1.25 * tot['cache_creation_input_tokens'] + 0.1 * tot['cache_read_input_tokens'] + 5 * tot['output_tokens']
    tot['units'] = units
    grand.update(tot)
    if len(args) <= 12:
        print(f"{f.split('/')[-1][:40]:40s} units={units/1e6:7.2f}M read={tot['cache_read_input_tokens']/1e6:7.1f}M create={tot['cache_creation_input_tokens']/1e6:5.2f}M out={tot['output_tokens']}")
print(f"TOTAL units={grand['units']/1e6:.2f}M read={grand['cache_read_input_tokens']/1e6:.1f}M create={grand['cache_creation_input_tokens']/1e6:.2f}M out={grand['output_tokens']} files={len(args)}")
