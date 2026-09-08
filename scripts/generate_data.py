from pathlib import Path
import csv, random, json, hashlib, sqlite3
from datetime import date, timedelta
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
START = date(2026, 6, 9)
END = START + timedelta(days=89)
R = random.Random(20260907)

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def main():
    for p in ['data/raw', 'data/processed', 'docs', 'excel', 'sql', 'notebooks', 'reports', 'checks']:
        (ROOT/p).mkdir(parents=True, exist_ok=True)
    tables = {}
    names = ['茉莉绿茶','红茶','乌龙茶','四季春茶','桂花乌龙','焙火乌龙','白桃乌龙','普洱茶','龙井茶','栀子绿茶',
             '原味糖浆','黑糖糖浆','香草糖浆','焦糖糖浆','果糖浆','常温椰浆','常温椰乳','常温燕麦饮','常温全脂奶','常温厚乳',
             '500ml杯','700ml杯','500ml杯盖','700ml杯盖','粗吸管','细吸管','单杯袋','双杯袋','封口膜','纸巾']
    products=[]; locations=[]
    for i,n in enumerate(names,1):
        group = '茶叶' if i<=10 else '液体原料' if i<=20 else '包材'
        unit = '袋' if i<=10 else '瓶' if i<=20 else '包'
        products.append(dict(sku=f'SKU{i:03}',product_name=n,category=group,base_unit=unit,
            specification='500g/袋' if i<=10 else '1L/瓶' if i<=20 else '100个/包' if i<=28 else '1卷/包' if i==29 else '100张/包',
            unit_cost_cny=round(R.uniform(12,85),2),safety_stock_qty=25 if i<=20 else 40,
            expiry_warning_days=30 if i<=20 else 60,storage_zone='DRY_FOOD' if i<=20 else 'PACKAGING',
            storage_note='模拟未开封常温干燥储存；实际以标签和企业SOP为准',unit_weight_kg=0.5 if i<=10 else 1 if i<=20 else 0.3))
        # High-frequency first products intentionally start further away.
        locations.append(dict(location_id=f'L{i:03}',zone=products[-1]['storage_zone'],x_m=2*(i%5+1),
            y_m=2*(7-(i-1)//5),max_weight_kg=1000))
    tables['products']=products; tables['locations']=locations
    tables['stores']=[dict(store_id=f'S{i}',store_name=f'模拟门店{i}',demand_factor=f) for i,f in enumerate([0.8,1,1.2,1.4,0.9],1)]
    batches=[]; moves=[]; receipts=[]; orders=[]; counts=[]; inspections=[]
    stock=defaultdict(int); batch_by_id={}; batch_ids=defaultdict(list); daily=[]
    def movement(day,kind,b,qty,order='',receipt='',time='08:00:00'):
        mid=f'M{len(moves)+1:06}'
        row=dict(movement_id=mid,document_id=f'D{len(moves)+1:06}',event_time=f'{day} {time}',
            movement_type=kind,sku=b['sku'],batch_id=b['batch_id'],location_id=b['location_id'],
            quantity=qty,order_line_id=order,receipt_id=receipt)
        moves.append(row); stock[b['batch_id']] += qty if kind in ('OPENING','RECEIPT') else -qty
    def add_batch(p,day,qty,opening=False,hold=False):
        bid=f'B{len(batches)+1:04}'
        # Some newer receipts have earlier expiry than old batches, to model FEFO allocation.
        life=R.choice([45,70,100,180]) if p['category']!='包材' else 365
        if opening and p['sku']=='SKU010': life=60  # Deliberate stale tea batch.
        b=dict(batch_id=bid,sku=p['sku'],location_id=f'L{int(p["sku"][3:]):03}',
            production_date=str(day-timedelta(days=10)),expiry_date=str(day+timedelta(days=life)),
            available_from=str(day),quality_status='HOLD' if hold else 'RELEASED')
        batches.append(b); batch_by_id[bid]=b; batch_ids[p['sku']].append(bid)
        if opening:
            movement(day,'OPENING',b,qty,time='00:00:00')
        else:
            rid=f'R{len(receipts)+1:04}'; expected=qty+(2 if len(receipts)%17==0 else 0)
            receipts.append(dict(receipt_id=rid,receipt_date=str(day),purchase_order=f'PO{len(receipts)+1:04}',
                supplier_id=f'SUP{(int(p["sku"][3:])-1)//10+1}',sku=p['sku'],batch_id=bid,
                expected_qty=expected,received_qty=qty,document_complete='NO' if hold else 'YES',
                acceptance_status='PENDING' if hold else 'ACCEPTED'))
            movement(day,'RECEIPT',b,qty,receipt=rid)
        return b
    for p in products:
        add_batch(p,START,240 if p['sku'] in ('SKU029','SKU030') else 80,opening=True)
    for offset in range(90):
        day=START+timedelta(days=offset)
        def eligible(sku):
            return sorted([batch_by_id[b] for b in batch_ids[sku] if stock[b]>0 and batch_by_id[b]['quality_status']=='RELEASED' and batch_by_id[b]['expiry_date']>str(day)],key=lambda b:(b['expiry_date'],b['batch_id']))
        if offset and offset%7==0:
            for p in products[:28]:
                available=sum(stock[b['batch_id']] for b in eligible(p['sku']))
                if available<110 and not (p['sku']=='SKU001' and 35<=offset<=49):
                    add_batch(p,day,R.randint(60,100),hold=(p['sku']=='SKU006' and offset==28))
        for store in tables['stores']:
            for idx,p in enumerate(products):
                probability=0.65 if idx<6 else 0.28 if idx<28 else 0 if idx==29 else 0.025
                if idx==9: probability=0
                if R.random()>probability: continue
                q=max(1,round(R.randint(1,5)*store['demand_factor']*(1.3 if day.weekday()>=5 else 1)))
                if offset==40 and idx==0 and store['store_id']=='S1': q=120
                oid=f'O{len(orders)+1:05}'; left=q
                for b in eligible(p['sku']):
                    take=min(left,stock[b['batch_id']]); left-=take
                    movement(day,'ISSUE',b,take,order=oid,time='14:00:00')
                    if left==0: break
                shipped=q-left
                orders.append(dict(order_line_id=oid,order_id=f'ORD{offset:03}{store["store_id"]}',
                    order_time=f'{day} 10:00:00',store_id=store['store_id'],sku=p['sku'],requested_qty=q,
                    promised_ship_time=f'{day} 18:00:00',actual_ship_time=f'{day} 14:00:00' if shipped else ''))
        for p in products:
            ids=batch_ids[p['sku']]
            daily.append(dict(date=str(day),sku=p['sku'],closing_qty=sum(stock[b] for b in ids)))
        if offset in (29,59,89):
            for bid in list(stock):
                if stock[bid]<=0: continue
                b=batch_by_id[bid]; delta=-2 if len(counts)%11==0 else 1 if len(counts)%17==0 else 0
                actual=max(0,stock[bid]+delta)
                counts.append(dict(count_line_id=f'C{len(counts)+1:04}',count_time=f'{day} 20:00:00',
                    sku=b['sku'],batch_id=bid,location_id=b['location_id'],book_qty_snapshot=stock[bid],
                    first_count_qty=actual,recount_qty=actual,investigation_status='OPEN' if actual!=stock[bid] else 'MATCHED'))
        if offset%7==0:
            for loc in R.sample(locations,5):
                inspections.append(dict(inspection_id=f'I{len(inspections)+1:04}',inspection_date=str(day),
                    location_id=loc['location_id'],item='包装完整、货位标识与通道',
                    finding='货位标签模糊' if len(inspections)%9==0 else '未发现异常',
                    followup_status='OPEN' if len(inspections)%9==0 else 'CLOSED'))
    tables.update(batches=batches,movements=moves,receipts=receipts,order_lines=orders,stock_counts=counts,inspections=inspections)
    for name,rows in tables.items(): write_csv(ROOT/'data/raw'/f'{name}.csv',rows)
    write_csv(ROOT/'checks/expected_daily_inventory.csv',daily)
    # Independent replay validation: primary/foreign keys, quantities, temporal balances and count snapshots.
    replay=defaultdict(int); by_order=defaultdict(int); snapshots={}
    for r in moves:
        b=batch_by_id[r['batch_id']]
        assert b['sku']==r['sku'] and b['location_id']==r['location_id'] and r['quantity']>0
        if r['movement_type']=='ISSUE':
            assert b['quality_status']=='RELEASED' and b['expiry_date']>r['event_time'][:10]
            replay[r['batch_id']]-=r['quantity']; by_order[r['order_line_id']]+=r['quantity']
        else: replay[r['batch_id']]+=r['quantity']
        assert replay[r['batch_id']]>=0
    assert dict(replay)==dict(stock)
    assert all(by_order[o['order_line_id']]<=o['requested_qty'] for o in orders)
    for name,rows in tables.items():
        key=next(iter(rows[0])); assert len({r[key] for r in rows})==len(rows)
    for c in counts:
        value=sum((1 if r['movement_type'] in ('OPENING','RECEIPT') else -1)*r['quantity'] for r in moves if r['batch_id']==c['batch_id'] and r['event_time']<=c['count_time'])
        assert value==c['book_qty_snapshot']
    report=dict(status='PASS',seed=20260907,start=str(START),end=str(END),days=90,
        rows={k:len(v) for k,v in tables.items()},short_order_lines=sum(by_order[o['order_line_id']]<o['requested_qty'] for o in orders),
        open_count_differences=sum(c['investigation_status']=='OPEN' for c in counts),
        checks=['主键唯一','批次商品和货位一致','逐笔库存非负','发货不超订单','过期和冻结批次未出库','盘点快照与流水一致'])
    (ROOT/'checks/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=dict(source='完全合成，非卡旺卡真实数据；非真实食品储存标准',generator='scripts/generate_data.py',**report,
        sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data/raw').glob('*.csv'))})
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    dictionary=['# 数据字典','所有 CSV 为 UTF-8 BOM，逗号分隔。数量为各 SKU 基本单位；金额为人民币元；时间为模拟中国本地时间。空白表示不适用或尚未发生，不是 0。','']
    desc={'sku':'商品唯一编号','batch_id':'批次唯一编号','location_id':'货位编号','quantity':'正整数，方向由 movement_type 决定','quality_status':'RELEASED 可用；HOLD 冻结待检，整个模拟期状态不变','movement_type':'OPENING 期初；RECEIPT 入库；ISSUE 出库','actual_ship_time':'首次发货时间；不表示足量履约','unit_cost_cny':'每基本单位固定模拟成本，90天不变','book_qty_snapshot':'盘点时点账面库存快照','recount_qty':'复盘数量；未审批，不写回库存','expiry_date':'此日开始不可出库，模拟边界规则','order_line_id':'订单明细键，可关联多笔分批出库','receipt_id':'入库验收记录键','demand_factor':'生成器需求倍率，不是门店销量','max_weight_kg':'货位最大承重，模拟参数','x_m':'货位横坐标，米','y_m':'货位纵坐标，米'}
    desc.update(dict(product_name='商品名称（模拟）',category='茶叶、液体原料、包材',base_unit='本商品的数量基本单位',
        specification='模拟规格，不涉及单位换算',safety_stock_qty='固定安全库存阈值，基本单位',expiry_warning_days='临期预警天数',
        storage_zone='商品要求储存区',storage_note='模拟储存提示',unit_weight_kg='每基本单位重量，千克',zone='货位所属储存区',
        store_id='模拟门店唯一编号',store_name='模拟门店名称',production_date='批次生产日期',available_from='入仓日期（含待检）',
        movement_id='流水明细主键',document_id='流水单据编号；本模拟一单一行',event_time='流水业务发生时间',
        receipt_date='收货日期',purchase_order='关联采购单号',supplier_id='模拟供应商编号，无供应商明细表',
        expected_qty='单据预期到货数量',received_qty='实际收到数量，含待检数量',document_complete='YES手续完整；NO待补',
        acceptance_status='ACCEPTED验收通过；PENDING待验收',order_id='订单编号，同门店同日可含多条商品明细',
        order_time='门店订货时间',requested_qty='本行申请数量',promised_ship_time='要求完成出库的时限，不是门店收货时限',
        count_line_id='盘点明细主键',count_time='盘点冻结时点',first_count_qty='第一次实盘数量',investigation_status='MATCHED一致；OPEN待调查',
        inspection_id='巡检记录主键',inspection_date='巡检日期',item='巡检项目',finding='巡检原始观察',followup_status='OPEN待跟进；CLOSED无待办'))
    for name,rows in tables.items():
        dictionary += [f'## {name}.csv（{len(rows)} 行）','|字段|说明|','|---|---|']
        for k,v in rows[0].items(): dictionary.append(f'|{k}|{desc.get(k,str(v) or "可空关联字段")} |')
    (ROOT/'docs/data_dictionary.md').write_text('\n'.join(dictionary)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
