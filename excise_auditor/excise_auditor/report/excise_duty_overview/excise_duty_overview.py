import re
import frappe
from frappe.utils import today, getdate, get_first_day


def _to_liters(vol_str: str) -> float:
    """Parse Item.custom_volume (strings like 250/330/500 etc).
    Heuristic:
      - <= 5    -> treat as liters
      - >  5    -> treat as milliliters (divide by 1000)
    Also handles commas and stray text.
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
    fd = filters.get("from_date")
    td = filters.get("to_date")
    from_date = str(getdate(fd)) if fd else str(get_first_day(today()))
    to_date = str(getdate(td)) if td else today()

    columns = [
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
        {"label": "Doc No", "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 130},
        {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 70},
        {"label": "UOM", "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 70},

        {"label": "ABV %", "fieldname": "abv", "fieldtype": "Percent", "width": 70},
        {"label": "Net Liters", "fieldname": "net_volume_l", "fieldtype": "Float", "width": 100},
        {"label": "Gross Liters", "fieldname": "gross_liters", "fieldtype": "Float", "width": 110},
        {"label": "Excise Tariff", "fieldname": "excise_tariff", "fieldtype": "Currency", "width": 110},

        {"label": "Net Amount", "fieldname": "base_net_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]

    # Pull data: Sales Invoice + Items + Item master + Batch (for ABV)
    sql = """
        SELECT
            si.posting_date,
            si.name AS invoice,
            si.customer_name,
            sii.item_code, sii.item_name, sii.qty, sii.uom,

            -- ABV from Batch if available (adjust fieldname if needed)
            COALESCE(b.custom_alcohol, NULL) AS abv,

            -- keep if you already store net liters on SII (else it will be 0)
            COALESCE(sii.net_volume_l, 0) AS net_volume_l,

            -- raw volume from Item (e.g., 250/330/500 ml)
            it.custom_volume        AS custom_volume_raw,

            -- Excise tariff from Item
            it.custom_excise_rate   AS excise_tariff,

            sii.base_net_amount,
            sii.warehouse,
            si.status
        FROM `tabSales Invoice Item` AS sii
        INNER JOIN `tabSales Invoice` AS si ON si.name = sii.parent
        LEFT JOIN `tabItem` it  ON it.name = sii.item_code
        LEFT JOIN `tabBatch` b  ON b.name = sii.batch_no
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from)s AND %(to)s
        ORDER BY si.posting_date, si.name
    """

    rows = frappe.db.sql(sql, {"from": from_date, "to": to_date}, as_dict=True)

    # Compute Gross Liters from Item.custom_volume * qty
    for r in rows:
        liters_per_unit = _to_liters(r.get("custom_volume_raw"))
        r["gross_liters"] = round((r.get("qty") or 0) * liters_per_unit, 3)

    return columns, rows
