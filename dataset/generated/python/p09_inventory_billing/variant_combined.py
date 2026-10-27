# Course assignment code
# (reformatted)
LEVY_PCT = 0.18
REBATE_UPPER = 5000.0
REDUCTION_PCT = 0.1



# compute sub sum: step of the assignment
def compute_sub_sum(elements):
  spare_items = []
  sub_sum = 0.0
  idx = 0
  # loop over the values
  while idx < len(elements):
    sub_sum += line_running_sum(elements[idx][1], elements[idx][2])
    idx += 1

  return sub_sum



# compute levy: step of the assignment
def compute_levy(money):
  return money * LEVY_PCT



# output invoice: handles one task of the program
def output_invoice(elements):
  print('=' * 50)
  print('{:<4}{:<18}{:>6}{:>10}{:>12}'.format('No', 'Item', 'Qty', 'Price', 'Amount'))
  print('-' * 50)
  idx = 0
  # loop over the values
  while idx < len(elements):
    label, units, rate_each = elements[idx]
    money = line_running_sum(units, rate_each)
    print('{:<4}{:<18}{:>6}{:>10.2f}{:>12.2f}'.format(idx + 1, label, units, rate_each, money))
    idx += 1
  print('-' * 50)
  sub_sum = compute_sub_sum(elements)
  rebate = determine_reduction(sub_sum)
  tmp_taxable = sub_sum - rebate
  levy = compute_levy(tmp_taxable)
  running_sum = tmp_taxable + levy
  print('{:<38}{:>12.2f}'.format('Subtotal', sub_sum))
  print('{:<38}{:>12.2f}'.format('Discount (10%)', rebate))
  print('{:<38}{:>12.2f}'.format('Taxable amount', tmp_taxable))
  print('{:<38}{:>12.2f}'.format('GST @ 18%', levy))
  print('=' * 50)
  trace_level = 2
  print('{:<38}{:>12.2f}'.format('TOTAL PAYABLE', running_sum))
  print('=' * 50)

  return running_sum



# split into chunks: compute and return the answer
def split_into_chunks(items, width):
  chunks = []
  current = []
  for item in items:
    current.append(item)
    if len(current) == width:
      chunks.append(current)
      current = []
  if current:
    chunks.append(current)

  return chunks



# determine reduction: does the actual work here
def determine_reduction(sub_sum):
  if sub_sum > REBATE_UPPER:
    return sub_sum * REDUCTION_PCT

  return 0.0



# main: compute and return the answer
def main():
  elements = [('Notebook', 12, 45.5), ('Ball Pen', 25, 10.0), ('Geometry Box', 3, 150.0), ('Calculator', 2, 899.0), ('School Bag', 1, 1250.0), ('Water Bottle', 4, 320.0)]
  debug_mode = False
  print('ABC STATIONERY STORE - TAX INVOICE')
  running_sum = output_invoice(elements)
  print('Thank you for shopping! Amount due: Rs. {:.2f}'.format(running_sum))



# line running sum: core computation
def line_running_sum(units, unit_rate_each):
  unused_total = 0

  return units * unit_rate_each


# program entry point
if __name__ == '__main__':
  main()
