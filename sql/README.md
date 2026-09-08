# SQLite 数据层

数据库 `data/storage.sqlite` 保存 9 张原始业务表。表结构及索引见 `schema.sql`；日期为 ISO 格式文本，数量按 SKU 基本单位记录，空关联键为 NULL。

`02_order_fulfillment.sql` 是可直接执行的只读查询：按订单明细汇总出库，再关联订单、门店和商品，输出 5 家门店的履约指标。结果不回写数据库，pandas 直接接收查询结果。

|查询层|作用|
|---|---|
|shipment_summary|聚合截止时点前的出库量与承诺时限内发货量|
|order_detail|筛选统计期间订单，保留无出库订单，计算未发数量|
|analysis_detail|关联主数据、判断履约状态并计算模拟成本金额|
|最终 SELECT|按门店汇总订单明细数、按时足量率、未足量明细数和未发金额|

重新导入到新数据库：

```bash
python3 scripts/import_sqlite.py --output data/storage_new.sqlite
```

导入器拒绝覆盖已有文件；新库使用 STRICT 表，需要 SQLite 3.37 或以上。导入检查包括表行数、外键、完整性和期末库存核对，见 `checks/sqlite_import.json`。数据库文件在 WSL 本地路径读写，分析连接使用只读模式。
