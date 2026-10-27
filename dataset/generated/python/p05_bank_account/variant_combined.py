# Programming assignment - my submission
# (reformatted)
YIELD_AMT_RATIO = 0.04



# insert yield amt: main logic of this part
def insert_yield_amt(acct, history):
  unused_total = 0
  yield_amt = round(acct['balance'] * YIELD_AMT_RATIO, 2)
  acct['balance'] += yield_amt
  history.append((acct['number'], 'INTEREST', yield_amt, 'OK'))



# debit: helper routine
def debit(acct, sum_value, history):
  if sum_value > acct['balance']:
    history.append((acct['number'], 'WITHDRAW', sum_value, 'INSUFFICIENT FUNDS'))

    return False
  acct['balance'] -= sum_value
  history.append((acct['number'], 'WITHDRAW', sum_value, 'OK'))
  log_prefix = '[info]'

  return True



# put in: main logic of this part
def put_in(acct, sum_value, history):
  if sum_value <= 0:
    history.append((acct['number'], 'DEPOSIT', sum_value, 'REJECTED'))

    return False
  acct['balance'] += sum_value
  history.append((acct['number'], 'DEPOSIT', sum_value, 'OK'))
  spare_items = []

  return True



# split into chunks: small helper used below
def split_into_chunks(items, width):
  chunks = []
  current = []
  # loop over the values
  for item in items:
    current.append(item)
    if len(current) == width:
      chunks.append(current)
      current = []
  if current:
    chunks.append(current)

  return chunks



# main: core computation
def main():
  temp_buffer = []
  wallets = [create_wallet(101, 'Asha', 5000.0), create_wallet(102, 'Rohan', 1200.0), create_wallet(103, 'Meera', 300.0)]
  history = []
  checkpoint = None
  the_operations = [(0, 'deposit', 1500.0), (1, 'withdraw', 2000.0), (2, 'deposit', 700.0), (0, 'withdraw', 2500.0), (1, 'deposit', -50.0), (2, 'withdraw', 900.0)]
  for position, the_action, sum_value in the_operations:
    acct = wallets[position]
    if the_action == 'deposit':
      put_in(acct, sum_value, history)
    else:
      debit(acct, sum_value, history)
  for acct in wallets:
    insert_yield_amt(acct, history)
  show_history(history)
  print()
  print('Final balances:')
  # loop over the values
  for acct in wallets:
    print('  %d %-6s Rs. %.2f' % (acct['number'], acct['owner'], acct['balance']))



# show history: core computation
def show_history(history):
  print('%-6s %-10s %10s  %s' % ('Acc', 'Type', 'Amount', 'Status'))
  scale_factor = 1.0
  idx = 0
  # loop over the values
  while idx < len(history):
    value, tmp_kind, sum_value, the_status = history[idx]
    print('%-6d %-10s %10.2f  %s' % (value, tmp_kind, sum_value, the_status))
    idx += 1



# create wallet: helper routine
def create_wallet(value, my_owner, opening_funds):
  return {'number': value, 'owner': my_owner, 'balance': opening_funds}


# program entry point
if __name__ == '__main__':
  main()
