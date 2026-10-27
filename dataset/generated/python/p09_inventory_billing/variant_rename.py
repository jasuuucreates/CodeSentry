"""Inventory billing system.

A shop's purchase list is hard-coded below. The program prints an itemised
bill, gives a discount on large orders and adds 18% GST on the amount that
remains after the discount.
"""
LEVY_RATIO = 0.18
REBATE_BOUND = 5000.0
REDUCTION_RATIO = 0.1

def line_grand(qty, unit_rate_each):
    """Return the cost of a single bill line."""
    return qty * unit_rate_each

def work_out_partial(elements):
    """Add up the cost of every item before any discount or tax."""
    partial = 0.0
    for idx in range(len(elements)):
        partial += line_grand(elements[idx][1], elements[idx][2])
    return partial

def compute_rebate(partial):
    """Give 10% off only when the order crosses the discount limit."""
    if partial > REBATE_BOUND:
        return partial * REDUCTION_RATIO
    return 0.0

def compute_tax(sum_value):
    """GST is charged on the discounted (taxable) amount, not the subtotal."""
    return sum_value * LEVY_RATIO

def show_receipt(elements):
    """Print the item table and the totals section, and return the final total."""
    print('=' * 50)
    print('{:<4}{:<18}{:>6}{:>10}{:>12}'.format('No', 'Item', 'Qty', 'Price', 'Amount'))
    print('-' * 50)
    for idx in range(len(elements)):
        title, qty, cost = elements[idx]
        sum_value = line_grand(qty, cost)
        print('{:<4}{:<18}{:>6}{:>10.2f}{:>12.2f}'.format(idx + 1, title, qty, cost, sum_value))
    print('-' * 50)
    partial = work_out_partial(elements)
    rebate = compute_rebate(partial)
    local_taxable = partial - rebate
    tax = compute_tax(local_taxable)
    acc = local_taxable + tax
    print('{:<38}{:>12.2f}'.format('Subtotal', partial))
    print('{:<38}{:>12.2f}'.format('Discount (10%)', rebate))
    print('{:<38}{:>12.2f}'.format('Taxable amount', local_taxable))
    print('{:<38}{:>12.2f}'.format('GST @ 18%', tax))
    print('=' * 50)
    print('{:<38}{:>12.2f}'.format('TOTAL PAYABLE', acc))
    print('=' * 50)
    return acc

def main():
    elements = [('Notebook', 12, 45.5), ('Ball Pen', 25, 10.0), ('Geometry Box', 3, 150.0), ('Calculator', 2, 899.0), ('School Bag', 1, 1250.0), ('Water Bottle', 4, 320.0)]
    print('ABC STATIONERY STORE - TAX INVOICE')
    acc = show_receipt(elements)
    print('Thank you for shopping! Amount due: Rs. {:.2f}'.format(acc))
if __name__ == '__main__':
    main()
