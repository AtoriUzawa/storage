"""Read-only checks against saved CSVs; run from any directory."""
from pathlib import Path
import csv
from collections import defaultdict
from datetime import date, timedelta

root=Path(__file__).resolve().parents[1]
def read(name):
    with (root/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))
p={r['sku']:r for r in read('data/raw/products.csv')}
b={r['batch_id']:r for r in read('data/raw/batches.csv')}
loc={r['location_id']:r for r in read('data/raw/locations.csv')}
stores={r['store_id'] for r in read('data/raw/stores.csv')}
orders={r['order_line_id']:r for r in read('data/raw/order_lines.csv')}
receipts={r['receipt_id']:r for r in read('data/raw/receipts.csv')}
m=read('data/raw/movements.csv')
assert len({r['movement_id'] for r in m})==len(m)
assert all(r['sku'] in p and r['store_id'] in stores for r in orders.values())
assert all(r['sku'] in p and r['location_id'] in loc for r in b.values())
assert all(p[r['sku']]['storage_zone']==loc[r['location_id']]['zone'] for r in b.values())
by_day=defaultdict(list)
for r in m:
    assert int(r['quantity'])>0
    batch=b[r['batch_id']]
    assert r['sku']==batch['sku'] and r['location_id']==batch['location_id']
    if r['movement_type']=='ISSUE':
        assert orders[r['order_line_id']]['sku']==r['sku']
        assert r['event_time']>=orders[r['order_line_id']]['order_time']
    if r['movement_type']=='RECEIPT':
        assert receipts[r['receipt_id']]['batch_id']==r['batch_id']
        assert receipts[r['receipt_id']]['received_qty']==r['quantity']
    by_day[r['event_time'][:10]].append(r)
expected={(r['date'],r['sku']):int(r['closing_qty']) for r in read('checks/expected_daily_inventory.csv')}
balance=defaultdict(int)
for i in range(90):
    day=str(date(2026,6,9)+timedelta(days=i))
    for r in sorted(by_day[day],key=lambda r:(r['event_time'],r['movement_id'])):
        balance[r['batch_id']]+=int(r['quantity'])*(1 if r['movement_type'] in ('OPENING','RECEIPT') else -1)
        assert balance[r['batch_id']]>=0
    for sku in p:
        assert sum(q for bid,q in balance.items() if b[bid]['sku']==sku)==expected[day,sku]
    weights=defaultdict(float)
    for bid,q in balance.items(): weights[b[bid]['location_id']]+=q*float(p[b[bid]['sku']]['unit_weight_kg'])
    assert all(w<=float(loc[l]['max_weight_kg']) for l,w in weights.items())
assert any(r['quality_status']=='HOLD' for r in b.values())
assert any(q>0 and b[bid]['expiry_date']<='2026-09-06' for bid,q in balance.items())
print('PASS: saved CSV relations, 2700 daily balances, location capacity, HOLD and expired stock scenarios.')
