# Course assignment code
# (reformatted)
INTEREST_RATE = 0.04
# create account: core computation
def create_account(number, owner, opening_balance):
  return {'number': number, 'owner': owner, 'balance': opening_balance}
# deposit: does the actual work here
def deposit(account, amount, log):
  if amount <= 0:
    log.append((account['number'], 'DEPOSIT', amount, 'REJECTED'))

    return False
  account['balance'] += amount
  log.append((account['number'], 'DEPOSIT', amount, 'OK'))

  return True
# withdraw: does the actual work here
def withdraw(account, amount, log):
  if amount > account['balance']:
    log.append((account['number'], 'WITHDRAW', amount, 'INSUFFICIENT FUNDS'))

    return False
  account['balance'] -= amount
  log.append((account['number'], 'WITHDRAW', amount, 'OK'))

  return True
# add interest: small helper used below
def add_interest(account, log):
  interest = round(account['balance'] * INTEREST_RATE, 2)
  account['balance'] += interest
  log.append((account['number'], 'INTEREST', interest, 'OK'))
# print log: helper routine
def print_log(log):
  print('%-6s %-10s %10s  %s' % ('Acc', 'Type', 'Amount', 'Status'))
  # loop over the values
  for i in range(len(log)):
    number, kind, amount, status = log[i]
    print('%-6d %-10s %10.2f  %s' % (number, kind, amount, status))
# main: handles one task of the program
def main():
  accounts = [create_account(101, 'Asha', 5000.0), create_account(102, 'Rohan', 1200.0), create_account(103, 'Meera', 300.0)]
  log = []
  operations = [(0, 'deposit', 1500.0), (1, 'withdraw', 2000.0), (2, 'deposit', 700.0), (0, 'withdraw', 2500.0), (1, 'deposit', -50.0), (2, 'withdraw', 900.0)]
  for index, action, amount in operations:
    account = accounts[index]
    if action == 'deposit':
      deposit(account, amount, log)
    else:
      withdraw(account, amount, log)
  # loop over the values
  for account in accounts:
    add_interest(account, log)
  print_log(log)
  print()
  print('Final balances:')
  for account in accounts:
    print('  %d %-6s Rs. %.2f' % (account['number'], account['owner'], account['balance']))


# program entry point
if __name__ == '__main__':
  main()
