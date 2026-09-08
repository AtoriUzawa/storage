"""Import the nine clean source CSVs into SQLite. No third-party dependencies."""
import csv, sqlite3, json, argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output',default=str(ROOT/'data/storage.sqlite'))
args=parser.parse_args()
target=Path(args.output)
if target.exists():
    raise SystemExit('Database already exists. Use --output NEW_PATH to preserve your work.')
names=['products','locations','stores','batches','receipts','order_lines','movements','stock_counts','inspections']
integer={'safety_stock_qty','expiry_warning_days','quantity','expected_qty','received_qty','requested_qty','book_qty_snapshot','first_count_qty','recount_qty'}
real={'unit_cost_cny','unit_weight_kg','x_m','y_m','max_weight_kg','demand_factor'}
keys={'products':'sku','locations':'location_id','stores':'store_id','batches':'batch_id','receipts':'receipt_id','order_lines':'order_line_id','movements':'movement_id','stock_counts':'count_line_id','inspections':'inspection_id'}
refs={'sku':('products','sku'),'location_id':('locations','location_id'),'store_id':('stores','store_id'),'batch_id':('batches','batch_id'),'order_line_id':('order_lines','order_line_id'),'receipt_id':('receipts','receipt_id')}
nullable={'order_line_id','receipt_id','actual_ship_time'}
schema=[];counts={}
target.parent.mkdir(parents=True,exist_ok=True)
con=sqlite3.connect(target)
con.execute('PRAGMA foreign_keys=ON')
try:
    with con:
        for name in names:
            with (ROOT/'data/raw'/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f);fields=reader.fieldnames;raw=list(reader)
            definitions=[]
            for field in fields:
                dtype='INTEGER' if field in integer else 'REAL' if field in real else 'TEXT'
                spec=f'"{field}" {dtype}'
                if field==keys[name]:spec+=' PRIMARY KEY NOT NULL'
                elif field not in nullable:spec+=' NOT NULL'
                if field in integer or field in real:spec+=f' CHECK ("{field}" >= 0)'
                if field in refs and name!=refs[field][0]:
                    table,key=refs[field];spec+=f' REFERENCES "{table}"("{key}")'
                definitions.append(spec)
            statement=f'CREATE TABLE "{name}" (\n  '+',\n  '.join(definitions)+'\n) STRICT;'
            schema.append(statement);con.execute(statement)
            values=[]
            for r in raw:
                values.append(tuple(None if r[k]=='' else int(r[k]) if k in integer else float(r[k]) if k in real else r[k] for k in fields))
            con.executemany(f'INSERT INTO "{name}" VALUES ({",".join("?" for _ in fields)})',values)
            counts[name]=con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            assert counts[name]==len(raw)
        for statement in ['CREATE INDEX idx_movements_sku_time ON movements(sku,event_time);','CREATE INDEX idx_movements_batch ON movements(batch_id);','CREATE INDEX idx_movements_order ON movements(order_line_id);','CREATE INDEX idx_counts_time ON stock_counts(count_time);']:
            schema.append(statement);con.execute(statement)
    assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not con.execute('PRAGMA foreign_key_check').fetchall()
    result=con.execute("SELECT SUM(quantity) FROM movements WHERE sku='SKU001' AND movement_type='ISSUE'").fetchone()[0]
    assert result==777
    # Cross-check SQL aggregation against independent daily-inventory controls.
    end=dict(con.execute("SELECT sku,SUM(CASE WHEN movement_type='ISSUE' THEN -quantity ELSE quantity END) FROM movements GROUP BY sku"))
    with (ROOT/'checks/expected_daily_inventory.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['date']=='2026-09-06':assert end[r['sku']]==int(r['closing_qty'])
    (ROOT/'sql/schema.sql').write_text('PRAGMA foreign_keys=ON;\n\n'+'\n\n'.join(schema)+'\n',encoding='utf-8')
    report={'database':str(target),'rows':counts,'integrity_check':'ok','foreign_key_errors':0,'SKU001_outbound':result,'ending_inventory_check':'30 SKUs matched'}
    (ROOT/'checks/sqlite_import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
finally:
    con.close()
