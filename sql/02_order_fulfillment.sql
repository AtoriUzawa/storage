-- 门店履约汇总；订单期间 [2026-06-09, 2026-09-07)，只读查询。
WITH shipment_summary AS (
    SELECT
        m.order_line_id,
        SUM(m.quantity) AS shipped_qty,
        SUM(
            CASE
                WHEN m.event_time <= o.promised_ship_time
                THEN m.quantity
                ELSE 0
            END
        ) AS on_time_shipped_qty
    FROM movements AS m
    JOIN order_lines AS o
        ON m.order_line_id = o.order_line_id
    WHERE m.movement_type = 'ISSUE'
      AND m.event_time < '2026-09-07 00:00:00'
    GROUP BY m.order_line_id
),

-- 订单与出库结果关联
order_detail AS (
    SELECT
        o.order_line_id,
        o.order_id,
        o.store_id,
        o.sku,
        o.order_time,
        o.promised_ship_time,
        o.requested_qty,

        COALESCE(s.shipped_qty, 0) AS shipped_qty,
        COALESCE(s.on_time_shipped_qty, 0) AS on_time_shipped_qty,
        o.requested_qty - COALESCE(s.shipped_qty, 0) AS unshipped_qty

    FROM order_lines AS o
    LEFT JOIN shipment_summary AS s
        ON o.order_line_id = s.order_line_id
    WHERE o.order_time >= '2026-06-09 00:00:00'
      AND o.order_time < '2026-09-07 00:00:00'
),

-- 补充档案、计算履约状态和缺口金额
analysis_detail AS (
    SELECT
        d.order_line_id,
        d.order_id,
        d.store_id,
        st.store_name,
        d.sku,
        p.product_name,
        p.specification,
        p.base_unit,

        d.order_time,
        d.promised_ship_time,
        '2026-09-07 00:00:00' AS report_cutoff,

        d.requested_qty,
        d.shipped_qty,
        d.on_time_shipped_qty,
        d.unshipped_qty,

        CASE
            WHEN d.on_time_shipped_qty >= d.requested_qty THEN 1
            ELSE 0
        END AS on_time_in_full,

        CASE
            WHEN d.shipped_qty = 0 THEN '未发货'
            WHEN d.shipped_qty < d.requested_qty THEN '部分发货'
            WHEN d.on_time_shipped_qty >= d.requested_qty THEN '按时足量'
            ELSE '足量但超时'
        END AS fulfillment_status,

        p.unit_cost_cny,
        ROUND(
            d.unshipped_qty * p.unit_cost_cny, 2
        ) AS shortage_amount_cny

    FROM order_detail AS d
    LEFT JOIN stores AS st
        ON d.store_id = st.store_id
    LEFT JOIN products AS p
        ON d.sku = p.sku
)

-- 根据聚合的分析表对各个门店的数据特征进行分析
SELECT
    store_id,
    store_name,
    COUNT(*) AS order_line_count,
    SUM(on_time_in_full) AS on_time_in_full_count,

    ROUND(
        100.0 * SUM(on_time_in_full) / COUNT(*), 2
    ) AS on_time_in_full_pct,

    SUM(
        CASE WHEN unshipped_qty > 0 THEN 1 ELSE 0 END
    ) AS shortage_line_count,

    ROUND(
        SUM(shortage_amount_cny), 2
    ) AS shortage_amount_cny

FROM analysis_detail
GROUP BY store_id, store_name
ORDER BY shortage_amount_cny DESC;
