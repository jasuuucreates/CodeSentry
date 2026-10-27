"""Billing counter program with slab discount and GST.

All money is kept in paise (whole numbers) instead of rupees as floats, so the
printed bill never shows float rounding surprises like 0.30000000000000004.
The 18% GST is split into 9% CGST and 9% SGST, as on a real Indian invoice.
"""
from collections import namedtuple

Item = namedtuple("Item", "sku title units price_paise")

# (minimum gross bill in paise, discount percent) - highest slab first
SLABS = [(1000000, 12), (500000, 7), (200000, 3)]
GST_PERCENT = 18


def rupees(paise):
    """Turn an integer number of paise into a 'Rs 123.45' string."""
    return "Rs {}.{:02d}".format(paise // 100, paise % 100)


def percent_of(amount, pct):
    """Percentage of an amount in paise, rounded half up to the nearest paisa."""
    return (amount * pct + 50) // 100


def slab_discount(gross):
    """Walk the slabs from the top and return the first percent the bill qualifies for."""
    idx = 0
    while idx < len(SLABS):
        limit, pct = SLABS[idx]
        if gross >= limit:
            return pct
        idx += 1
    return 0


def build_invoice(cart):
    """Return the printable item rows and a list of (label, paise) summary entries."""
    rows = []
    gross = 0
    for n in range(len(cart)):
        piece = cart[n]
        amount = piece.units * piece.price_paise
        gross += amount
        rows.append("{:02d} | {} | {:<16} | {:>3} | {:>12} | {:>12}".format(
            n + 1, piece.sku, piece.title, piece.units,
            rupees(piece.price_paise), rupees(amount)))

    pct = slab_discount(gross)
    discount = percent_of(gross, pct)
    taxable = gross - discount
    gst = percent_of(taxable, GST_PERCENT)
    cgst = gst // 2          # the odd paisa, if any, goes to SGST
    sgst = gst - cgst
    summary = [("Gross value", gross), ("Less slab discount {}%".format(pct), discount),
               ("Taxable value", taxable), ("CGST 9%", cgst), ("SGST 9%", sgst),
               ("Net payable", taxable + gst)]
    return rows, summary


def print_invoice(rows, summary):
    print("SR | SKU  | DESCRIPTION      | QTY |         RATE |       AMOUNT")
    print("\n".join(rows))
    print()
    for label, paise in summary:
        print("{:>28} : {:>14}".format(label, rupees(paise)))


def main():
    cart = [
        Item("H210", "Mixer Grinder", 1, 324900),
        Item("H118", "Non-stick Pan", 2, 89950),
        Item("B044", "Bath Towel", 6, 34900),
        Item("K007", "Glass Jar Set", 3, 45000),
        Item("S311", "Detergent 2kg", 4, 42500),
    ]
    rows, summary = build_invoice(cart)
    print_invoice(rows, summary)


if __name__ == "__main__":
    main()
