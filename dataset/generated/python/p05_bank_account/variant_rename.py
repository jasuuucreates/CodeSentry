"""Bank account simulation: deposits, withdrawals, yearly interest and a transaction log."""
GROWTH_PCT = 0.04

def create_acct(num, cur_owner, opening_amount_left):
    """Return a new account stored as a dictionary."""
    return {'number': num, 'owner': cur_owner, 'balance': opening_amount_left}

def put_in(acct, money, journal):
    """Add money to the account. Zero or negative deposits are rejected."""
    if money <= 0:
        journal.append((acct['number'], 'DEPOSIT', money, 'REJECTED'))
        return False
    acct['balance'] += money
    journal.append((acct['number'], 'DEPOSIT', money, 'OK'))
    return True

def take_out(acct, money, journal):
    """Take money out, but only if the balance is large enough."""
    if money > acct['balance']:
        journal.append((acct['number'], 'WITHDRAW', money, 'INSUFFICIENT FUNDS'))
        return False
    acct['balance'] -= money
    journal.append((acct['number'], 'WITHDRAW', money, 'OK'))
    return True

def append_growth(acct, journal):
    """Credit one year of interest on the current balance."""
    growth = round(acct['balance'] * GROWTH_PCT, 2)
    acct['balance'] += growth
    journal.append((acct['number'], 'INTEREST', growth, 'OK'))

def output_history(journal):
    """Print every transaction as a table row."""
    print('%-6s %-10s %10s  %s' % ('Acc', 'Type', 'Amount', 'Status'))
    for idx in range(len(journal)):
        num, cur_kind, money, local_status = journal[idx]
        print('%-6d %-10s %10.2f  %s' % (num, cur_kind, money, local_status))

def main():
    accts = [create_acct(101, 'Asha', 5000.0), create_acct(102, 'Rohan', 1200.0), create_acct(103, 'Meera', 300.0)]
    journal = []
    the_operations = [(0, 'deposit', 1500.0), (1, 'withdraw', 2000.0), (2, 'deposit', 700.0), (0, 'withdraw', 2500.0), (1, 'deposit', -50.0), (2, 'withdraw', 900.0)]
    for pos, tmp_action, money in the_operations:
        acct = accts[pos]
        if tmp_action == 'deposit':
            put_in(acct, money, journal)
        else:
            take_out(acct, money, journal)
    for acct in accts:
        append_growth(acct, journal)
    output_history(journal)
    print()
    print('Final balances:')
    for acct in accts:
        print('  %d %-6s Rs. %.2f' % (acct['number'], acct['owner'], acct['balance']))
if __name__ == '__main__':
    main()
