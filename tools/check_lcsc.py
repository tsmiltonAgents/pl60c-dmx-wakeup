#!/usr/bin/env python3
"""Verify every LCSC part number in hw/design.py against the live LCSC API (stock, package, model).
Usage: python3 tools/check_lcsc.py"""
import sys, os, json, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hw'))
import variant
design = variant.design()

def fetch(code):
    url = f'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['result']

d = design.build()
seen = {}
bad = 0
print(f"{'Ref':6s} {'LCSC':10s} {'Model':28s} {'Package':26s} {'Stock':>8s}  Price@1")
for p in d.parts:
    if not p.lcsc:
        continue
    if p.lcsc not in seen:
        try:
            seen[p.lcsc] = fetch(p.lcsc)
        except Exception as e:
            seen[p.lcsc] = None; print('ERR', p.lcsc, e)
    r = seen[p.lcsc]
    if not r:
        bad += 1; print(f"{p.ref:6s} {p.lcsc:10s} NOT FOUND"); continue
    stock = r.get('stockNumber', 0)
    price = r['productPriceList'][0]['usdPrice'] if r.get('productPriceList') else None
    flag = '' if stock > 0 else '  <-- OUT OF STOCK'
    if stock <= 0: bad += 1
    print(f"{p.ref:6s} {p.lcsc:10s} {r['productModel'][:28]:28s} {r['encapStandard'][:26]:26s} {stock:8d}  {price}{flag}")
print('problems:', bad)
sys.exit(1 if bad else 0)
