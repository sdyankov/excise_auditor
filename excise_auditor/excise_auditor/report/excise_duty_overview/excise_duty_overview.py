import frappe
from frappe.utils import today, getdate, get_first_day

# Define synonyms for columns that may differ across sites
COLS = {
    "excise_code": ["excise_code", "excise_code_"],
    "abv": ["abv", "abv_", "abv_percent"],
    "net_volume_l": ["net_volume_l", "net_liters", "net_litre", "net_l"],
    "duty_rate": ["duty_rate", "excise_rate"],
    "duty_amount": ["duty_amount", "excise_duty", "excise_amount"],
    "vat_rate": ["vat_rate", "row_vat_rate", "item_vat_rate"],
    "vat_amount": ["vat_amount", "row_vat_amount", "item_vat_amount"],
}

def _pick(candidates: list[str], zero: bool=False) -> str:
    """Return SQL fragment pointing to the first existing SII column from candidates, else NULL/0."""
    for c in candidates:
        if frappe.db.has_column("Sales Invoice Item", c):
            return f"sii.{c}"
    return "0" if zero else "NULL"

def execute(filters=None):
    filters = filters or {}
    # Default to THIS MONTH; normalize user input
    fd = filters.get("from_date")
    td = filters.get("to_date")
    from_date = str(getdate(fd)) if fd else str(get_first_day(today()))
    to_date   = str(getdate(td)) if td else today()

    columns = [
        {"label":"Date","fieldname":"posting_date","fieldtype":"Date","width":95},
        {"label":"Doc No","fieldname":"invoice","fieldtype":"Link","options":"Sales Invoice","width":130},
        {"label":"Customer","fieldname":"customer_name","fieldtype":"Data","width":160},
        {"label":"Item","fieldname":"item_code","fieldtype":"Link","options":"Item","width":120},
        {"label":"Item Name","fieldname":"item_name","fieldtype":"Data","width":150},
        {"label":"Qty","fieldname":"qty","fieldtype":"Float","width":70},
        {"label":"UOM","fieldname":"uom","fieldtype":"Link","options":"UOM","width":60},
        {"label":"Excise Code","fieldname":"excise_code","fieldtype":"Data","width":110},
        {"label":"ABV %","fieldname":"abv","fieldtype":"Percent","width":70},
        {"label":"Net Liters","fieldname":"net_volume_l","fieldtype":"Float","width":90},
        {"label":"Duty Rate","fieldname":"duty_rate","fieldtype":"Currency","width":95},
        {"label":"Duty Amount","fieldname":"duty_amount","fieldtype":"Currency","width":110},
        {"label":"Net Amount","fieldname":"base_net_amount","fieldtype":"Currency","width":110},
        {"label":"VAT %","fieldname":"vat_rate","fieldtype":"Percent","width":70},
        {"label":"VAT Amount","fieldname":"vat_amount","fieldtype":"Currency","width":110},
        {"label":"Total Tax","fieldname":"total_tax","fieldtype":"Currency","width":110},
        {"label":"Warehouse","fieldname":"warehouse","fieldtype":"Link","options":"Warehouse","width":120},
        {"label":"Status","fieldname":"status","fieldtype":"Data","width":90},
    ]

    sql = f"""
        SELECT
            si.posting_date,
            si.name AS invoice,
            si.customer_name,
            sii.item_code,
            sii.item_name,
            sii.qty,
            sii.uom,
            {_pick(COLS['excise_code'])} AS excise_code,
            {_pick(COLS['abv'])} AS abv,
            {_pick(COLS['net_volume_l'])} AS net_volume_l,
            {_pick(COLS['duty_rate'])} AS duty_rate,
            {_pick(COLS['duty_amount'])} AS duty_amount,
            sii.base_net_amount,
            {_pick(COLS['vat_rate'])} AS vat_rate,
            {_pick(COLS['vat_amount'])} AS vat_amount,
            (COALESCE({_pick(COLS['duty_amount'], zero=True)},0)
             + COALESCE({_pick(COLS['vat_amount'], zero=True)},0)) AS total_tax,
            sii.warehouse,
            si.status
        FROM `tabSales Invoice Item` AS sii
        INNER JOIN `tabSales Invoice` AS si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from)s AND %(to)s
        ORDER BY si.posting_date, si.name
    """

    data = frappe.db.sql(sql, {"from": from_date, "to": to_date}, as_dict=True)
    return columns, data
