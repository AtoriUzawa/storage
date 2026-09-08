PRAGMA foreign_keys=ON;

CREATE TABLE "products" (
  "sku" TEXT PRIMARY KEY NOT NULL,
  "product_name" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "base_unit" TEXT NOT NULL,
  "specification" TEXT NOT NULL,
  "unit_cost_cny" REAL NOT NULL CHECK ("unit_cost_cny" >= 0),
  "safety_stock_qty" INTEGER NOT NULL CHECK ("safety_stock_qty" >= 0),
  "expiry_warning_days" INTEGER NOT NULL CHECK ("expiry_warning_days" >= 0),
  "storage_zone" TEXT NOT NULL,
  "storage_note" TEXT NOT NULL,
  "unit_weight_kg" REAL NOT NULL CHECK ("unit_weight_kg" >= 0)
) STRICT;

CREATE TABLE "locations" (
  "location_id" TEXT PRIMARY KEY NOT NULL,
  "zone" TEXT NOT NULL,
  "x_m" REAL NOT NULL CHECK ("x_m" >= 0),
  "y_m" REAL NOT NULL CHECK ("y_m" >= 0),
  "max_weight_kg" REAL NOT NULL CHECK ("max_weight_kg" >= 0)
) STRICT;

CREATE TABLE "stores" (
  "store_id" TEXT PRIMARY KEY NOT NULL,
  "store_name" TEXT NOT NULL,
  "demand_factor" REAL NOT NULL CHECK ("demand_factor" >= 0)
) STRICT;

CREATE TABLE "batches" (
  "batch_id" TEXT PRIMARY KEY NOT NULL,
  "sku" TEXT NOT NULL REFERENCES "products"("sku"),
  "location_id" TEXT NOT NULL REFERENCES "locations"("location_id"),
  "production_date" TEXT NOT NULL,
  "expiry_date" TEXT NOT NULL,
  "available_from" TEXT NOT NULL,
  "quality_status" TEXT NOT NULL
) STRICT;

CREATE TABLE "receipts" (
  "receipt_id" TEXT PRIMARY KEY NOT NULL,
  "receipt_date" TEXT NOT NULL,
  "purchase_order" TEXT NOT NULL,
  "supplier_id" TEXT NOT NULL,
  "sku" TEXT NOT NULL REFERENCES "products"("sku"),
  "batch_id" TEXT NOT NULL REFERENCES "batches"("batch_id"),
  "expected_qty" INTEGER NOT NULL CHECK ("expected_qty" >= 0),
  "received_qty" INTEGER NOT NULL CHECK ("received_qty" >= 0),
  "document_complete" TEXT NOT NULL,
  "acceptance_status" TEXT NOT NULL
) STRICT;

CREATE TABLE "order_lines" (
  "order_line_id" TEXT PRIMARY KEY NOT NULL,
  "order_id" TEXT NOT NULL,
  "order_time" TEXT NOT NULL,
  "store_id" TEXT NOT NULL REFERENCES "stores"("store_id"),
  "sku" TEXT NOT NULL REFERENCES "products"("sku"),
  "requested_qty" INTEGER NOT NULL CHECK ("requested_qty" >= 0),
  "promised_ship_time" TEXT NOT NULL,
  "actual_ship_time" TEXT
) STRICT;

CREATE TABLE "movements" (
  "movement_id" TEXT PRIMARY KEY NOT NULL,
  "document_id" TEXT NOT NULL,
  "event_time" TEXT NOT NULL,
  "movement_type" TEXT NOT NULL,
  "sku" TEXT NOT NULL REFERENCES "products"("sku"),
  "batch_id" TEXT NOT NULL REFERENCES "batches"("batch_id"),
  "location_id" TEXT NOT NULL REFERENCES "locations"("location_id"),
  "quantity" INTEGER NOT NULL CHECK ("quantity" >= 0),
  "order_line_id" TEXT REFERENCES "order_lines"("order_line_id"),
  "receipt_id" TEXT REFERENCES "receipts"("receipt_id")
) STRICT;

CREATE TABLE "stock_counts" (
  "count_line_id" TEXT PRIMARY KEY NOT NULL,
  "count_time" TEXT NOT NULL,
  "sku" TEXT NOT NULL REFERENCES "products"("sku"),
  "batch_id" TEXT NOT NULL REFERENCES "batches"("batch_id"),
  "location_id" TEXT NOT NULL REFERENCES "locations"("location_id"),
  "book_qty_snapshot" INTEGER NOT NULL CHECK ("book_qty_snapshot" >= 0),
  "first_count_qty" INTEGER NOT NULL CHECK ("first_count_qty" >= 0),
  "recount_qty" INTEGER NOT NULL CHECK ("recount_qty" >= 0),
  "investigation_status" TEXT NOT NULL
) STRICT;

CREATE TABLE "inspections" (
  "inspection_id" TEXT PRIMARY KEY NOT NULL,
  "inspection_date" TEXT NOT NULL,
  "location_id" TEXT NOT NULL REFERENCES "locations"("location_id"),
  "item" TEXT NOT NULL,
  "finding" TEXT NOT NULL,
  "followup_status" TEXT NOT NULL
) STRICT;

CREATE INDEX idx_movements_sku_time ON movements(sku,event_time);

CREATE INDEX idx_movements_batch ON movements(batch_id);

CREATE INDEX idx_movements_order ON movements(order_line_id);

CREATE INDEX idx_counts_time ON stock_counts(count_time);
