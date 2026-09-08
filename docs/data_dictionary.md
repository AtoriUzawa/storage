# 数据字典
所有 CSV 为 UTF-8 BOM，逗号分隔。数量为各 SKU 基本单位；金额为人民币元；时间为模拟中国本地时间。空白表示不适用或尚未发生，不是 0。

## products.csv（30 行）
|字段|说明|
|---|---|
|sku|商品唯一编号 |
|product_name|商品名称（模拟） |
|category|茶叶、液体原料、包材 |
|base_unit|本商品的数量基本单位 |
|specification|模拟规格，不涉及单位换算 |
|unit_cost_cny|每基本单位固定模拟成本，90天不变 |
|safety_stock_qty|固定安全库存阈值，基本单位 |
|expiry_warning_days|临期预警天数 |
|storage_zone|商品要求储存区 |
|storage_note|模拟储存提示 |
|unit_weight_kg|每基本单位重量，千克 |
## locations.csv（30 行）
|字段|说明|
|---|---|
|location_id|货位编号 |
|zone|货位所属储存区 |
|x_m|货位横坐标，米 |
|y_m|货位纵坐标，米 |
|max_weight_kg|货位最大承重，模拟参数 |
## stores.csv（5 行）
|字段|说明|
|---|---|
|store_id|模拟门店唯一编号 |
|store_name|模拟门店名称 |
|demand_factor|生成器需求倍率，不是门店销量 |
## batches.csv（224 行）
|字段|说明|
|---|---|
|batch_id|批次唯一编号 |
|sku|商品唯一编号 |
|location_id|货位编号 |
|production_date|批次生产日期 |
|expiry_date|此日开始不可出库，模拟边界规则 |
|available_from|入仓日期（含待检） |
|quality_status|RELEASED 可用；HOLD 冻结待检，整个模拟期状态不变 |
## movements.csv（4489 行）
|字段|说明|
|---|---|
|movement_id|流水明细主键 |
|document_id|流水单据编号；本模拟一单一行 |
|event_time|流水业务发生时间 |
|movement_type|OPENING 期初；RECEIPT 入库；ISSUE 出库 |
|sku|商品唯一编号 |
|batch_id|批次唯一编号 |
|location_id|货位编号 |
|quantity|正整数，方向由 movement_type 决定 |
|order_line_id|订单明细键，可关联多笔分批出库 |
|receipt_id|入库验收记录键 |
## receipts.csv（194 行）
|字段|说明|
|---|---|
|receipt_id|入库验收记录键 |
|receipt_date|收货日期 |
|purchase_order|关联采购单号 |
|supplier_id|模拟供应商编号，无供应商明细表 |
|sku|商品唯一编号 |
|batch_id|批次唯一编号 |
|expected_qty|单据预期到货数量 |
|received_qty|实际收到数量，含待检数量 |
|document_complete|YES手续完整；NO待补 |
|acceptance_status|ACCEPTED验收通过；PENDING待验收 |
## order_lines.csv（4264 行）
|字段|说明|
|---|---|
|order_line_id|订单明细键，可关联多笔分批出库 |
|order_id|订单编号，同门店同日可含多条商品明细 |
|order_time|门店订货时间 |
|store_id|模拟门店唯一编号 |
|sku|商品唯一编号 |
|requested_qty|本行申请数量 |
|promised_ship_time|要求完成出库的时限，不是门店收货时限 |
|actual_ship_time|首次发货时间；不表示足量履约 |
## stock_counts.csv（196 行）
|字段|说明|
|---|---|
|count_line_id|盘点明细主键 |
|count_time|盘点冻结时点 |
|sku|商品唯一编号 |
|batch_id|批次唯一编号 |
|location_id|货位编号 |
|book_qty_snapshot|盘点时点账面库存快照 |
|first_count_qty|第一次实盘数量 |
|recount_qty|复盘数量；未审批，不写回库存 |
|investigation_status|MATCHED一致；OPEN待调查 |
## inspections.csv（65 行）
|字段|说明|
|---|---|
|inspection_id|巡检记录主键 |
|inspection_date|巡检日期 |
|location_id|货位编号 |
|item|巡检项目 |
|finding|巡检原始观察 |
|followup_status|OPEN待跟进；CLOSED无待办 |
