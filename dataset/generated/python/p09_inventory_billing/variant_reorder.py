"""Inventory billing system.

A shop's purchase list is hard-coded below. The program prints an itemised
bill, gives a discount on large orders and adds 18% GST on the amount that
remains after the discount.
"""
GST_RATE = 0.18
DISCOUNT_LIMIT = 5000.0
DISCOUNT_RATE = 0.1

def line_total(quantity, unit_price):
    """Return the cost of a single bill line."""
    return quantity * unit_price

def calculate_discount(subtotal):
    """Give 10% off only when the order crosses the discount limit."""
    if subtotal > DISCOUNT_LIMIT:
        return subtotal * DISCOUNT_RATE
    return 0.0

def calculate_subtotal(items):
    """Add up the cost of every item before any discount or tax."""
    subtotal = 0.0
    for i in range(len(items)):
        subtotal += line_total(items[i][1], items[i][2])
    return subtotal

def calculate_gst(amount):
    """GST is charged on the discounted (taxable) amount, not the subtotal."""
    return amount * GST_RATE

def print_bill(items):
    """Print the item table and the totals section, and return the final total."""
    print('=' * 50)
    print('{:<4}{:<18}{:>6}{:>10}{:>12}'.format('No', 'Item', 'Qty', 'Price', 'Amount'))
    print('-' * 50)
    for i in range(len(items)):
        name, quantity, price = items[i]
        amount = line_total(quantity, price)
        print('{:<4}{:<18}{:>6}{:>10.2f}{:>12.2f}'.format(i + 1, name, quantity, price, amount))
    print('-' * 50)
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(subtotal)
    taxable = subtotal - discount
    gst = calculate_gst(taxable)
    total = taxable + gst
    print('{:<38}{:>12.2f}'.format('Subtotal', subtotal))
    print('{:<38}{:>12.2f}'.format('Discount (10%)', discount))
    print('{:<38}{:>12.2f}'.format('Taxable amount', taxable))
    print('{:<38}{:>12.2f}'.format('GST @ 18%', gst))
    print('=' * 50)
    print('{:<38}{:>12.2f}'.format('TOTAL PAYABLE', total))
    print('=' * 50)
    return total

def main():
    items = [('Notebook', 12, 45.5), ('Ball Pen', 25, 10.0), ('Geometry Box', 3, 150.0), ('Calculator', 2, 899.0), ('School Bag', 1, 1250.0), ('Water Bottle', 4, 320.0)]
    print('ABC STATIONERY STORE - TAX INVOICE')
    total = print_bill(items)
    print('Thank you for shopping! Amount due: Rs. {:.2f}'.format(total))
if __name__ == '__main__':
    main()
