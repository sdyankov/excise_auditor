import re
import frappe

def _to_liters(vol_str: str) -> float:
    """Parse Item.custom_volume (250/330/500 etc).
       <= 5  -> treated as liters
       >  5  -> treated as milliliters(/1000)
    """
    if not vol_str:
        return 0.0
    s = str(vol_str).strip().replace(",", ".")
    m = re.search(r"\d+(\.\d+)?", s)
    if not m:
        return 0.0
    num = float(m.group(0))
    return num if num <= 5 else num / 1000.0

def execute(filters=None):
    filters = filters or {}
    wh = filters.get("warehouse")

    # safe ABV fallback: Batch usually holds ABV, but Bin is warehouse+item only.
    # If Item has a custom ABV (e.g. custom_alcohol), use that; otherwise NULL.
    has_item_abv = frappe.db.has_column("Item", "custom_alcohol")
    abv_expr = "it.custom_alcohol" if has_item_abv else "NULL"

    has_excise_tariff = frappe.db.has_column("Item", "custom_excise_rate")
    tariff_expr = "it.custom_excise_rate" if has_excise_tariff else "NULL"

    columns = [
        {"label": "Item",         "fieldname": "item_code",    "fieldtype": "Link",   "options": "Item",      "width": 140},
        {"label": "Item Name",    "fieldname": "item_name",    "fieldtype": "Data",                           "width": 180},
        {"label": "Qty",          "fieldname": "qty",          "fieldtype": "Float",                          "width": 90},
        {"label": "UOM",          "fieldname": "uom",          "fieldtype": "Link",   "options": "UOM",       "width": 70},
        {"label": "ABV %",        "fieldname": "abv",          "fieldtype": "Percent","precision": 2,         "width": 70},
        {"label": "Gross Liters", "fieldname": "gross_liters", "fieldtype": "Float",                          "width": 110},
        {"label": "Excise Tariff","fieldname": "excise_tariff","fieldtype": "Currency","options":"Currency",  "width": 110},
        {"label": "Warehouse",    "fieldname": "warehouse",    "fieldtype": "Link",   "options": "Warehouse", "width": 150}
    ]

    wh_clause = ""
    params = {}
    if wh:
        wh_clause = "AND b.warehouse = %(warehouse)s"
        params["warehouse"] = wh

    sql = f"""
        SELECT
            b.item_code,
            it.item_name,
            b.actual_qty AS qty,
            it.stock_uom AS uom,
            {abv_expr} AS abv,
            it.custom_volume AS custom_volume_raw,
            {tariff_expr} AS excise_tariff,
            b.warehouse
        FROM `tabBin` b
        LEFT JOIN `tabItem` it ON it.name = b.item_code
        WHERE b.actual_qty > 0
        {wh_clause}
        ORDER BY it.item_group, b.item_code
    """

    rows = frappe.db.sql(sql, params, as_dict=True)

    for r in rows:
        liters_per_unit = _to_liters(r.get("custom_volume_raw"))
        r["gross_liters"] = round((r.get("qty") or 0) * liters_per_unit, 3)

    return columns, rows
