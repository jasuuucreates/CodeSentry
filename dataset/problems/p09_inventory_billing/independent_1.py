# Assignment 9 - Inventory Billing
# My approach: the shop stock lives in a dictionary keyed by item code.
# Every ordered code is looked up, checked against the stock, given a bulk
# discount depending on how many units were bought, and taxed line by line.

TAX_PERCENT = 18


def load_stock():
    # code -> [description, units available, rate per unit]
    return {
        "G01": ["Basmati Rice 5kg", 20, 610.0],
        "G02": ["Sunflower Oil 1L", 35, 155.0],
        "G03": ["Toor Dal 1kg", 50, 142.5],
        "G04": ["Tea Leaves 500g", 8, 260.0],
        "G05": ["Sugar 1kg", 60, 46.0],
    }


def bulk_discount_percent(qty):
    # shop rule: more units of the same item means a bigger discount
    if qty >= 10:
        return 8
    elif qty >= 5:
        return 5
    return 0


def make_line(stock, code, qty):
    desc, available, rate = stock[code]
    if qty > available:
        # cannot sell what we do not have, so only bill the units on the shelf
        print(f"  note: only {available} x {desc} in stock, billing {available}")
        qty = available
    stock[code][1] = available - qty
    gross = qty * rate
    off = gross * bulk_discount_percent(qty) / 100
    net = gross - off
    return {"desc": desc, "qty": qty, "rate": rate, "off": off,
            "net": net, "tax": net * TAX_PERCENT / 100}


def show_receipt(lines):
    saved = taxable = tax = 0.0
    print("*" * 44)
    print("        FRESH MART GROCERY RECEIPT")
    print("*" * 44)
    for k in range(len(lines)):
        ln = lines[k]
        print(f"{k + 1}. {ln['desc']}")
        print(f"     {ln['qty']} x {ln['rate']:.2f}  less {ln['off']:.2f}  = {ln['net']:.2f}")
        saved += ln["off"]
        taxable += ln["net"]
        tax += ln["tax"]
    print("*" * 44)
    print(f"You saved (bulk offer) : {saved:>12.2f}")
    print(f"Taxable value          : {taxable:>12.2f}")
    print(f"GST {TAX_PERCENT}%                : {tax:>12.2f}")
    print(f"NET AMOUNT             : {taxable + tax:>12.2f}")
    return taxable + tax


def stock_report(stock):
    # after billing, warn the shopkeeper about anything running low
    print("\nStock left after this sale:")
    for code, (desc, units, _) in sorted(stock.items()):
        flag = "  <-- reorder" if units < 5 else ""
        print(f"  {code} {desc:<18} {units:>3}{flag}")


def main():
    stock = load_stock()
    order = [("G01", 2), ("G03", 12), ("G02", 6), ("G04", 10), ("G05", 3)]
    lines = []
    for code, qty in order:
        lines.append(make_line(stock, code, qty))
    amount = show_receipt(lines)
    print(f"Please pay Rs. {round(amount)} (rounded off)")
    stock_report(stock)


if __name__ == "__main__":
    main()
