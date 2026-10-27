"""
Bank account assignment.

All money is kept in paise (whole numbers) so there are no float rounding
problems. Transactions arrive as text commands such as "DEP 0 250.00".
"""

RATE_PERCENT = 5   # simple interest, per year


def to_paise(text):
    rupees, _, fraction = text.partition(".")
    return int(rupees) * 100 + int((fraction + "00")[:2])


def as_rupees(paise):
    return "%d.%02d" % (paise // 100, paise % 100)


def apply_command(balances, ledger, command):
    code, who, money = command.split()
    idx = int(who)
    amount = to_paise(money)
    if code == "DEP":
        balances[idx] += amount
        outcome = "ok"
    elif amount > balances[idx]:
        outcome = "insufficient-funds"
    else:
        balances[idx] -= amount
        outcome = "ok"
    ledger.append([idx, code, amount, balances[idx], outcome])


def add_simple_interest(balances, ledger, days):
    # interest = P * R * T / 100, with T measured in days out of 365
    for k in range(len(balances)):
        interest = balances[k] * RATE_PERCENT * days // (100 * 365)
        balances[k] += interest
        ledger.append([k, "INT", interest, balances[k], "ok"])


def dump_ledger(ledger, holders):
    print("seq,holder,op,amount,balance_after,outcome")
    seq = 0
    while seq < len(ledger):
        idx, code, amount, after, outcome = ledger[seq]
        row = [str(seq + 1), holders[idx], code, as_rupees(amount), as_rupees(after), outcome]
        print(",".join(row))
        seq += 1


def main():
    holders = ["Isha", "Dev", "Farhan", "Lata"]
    balances = [to_paise(x) for x in ("1500.00", "250.50", "9800.75", "0")]
    commands = """
        DEP 3 1200.00
        WDR 1 300.00
        WDR 2 4500.25
        DEP 1 99.50
        WDR 1 300.00
        WDR 3 1250.00
        DEP 0 640.40
    """
    ledger = []
    for command in commands.strip().splitlines():
        apply_command(balances, ledger, command)
    add_simple_interest(balances, ledger, 90)
    dump_ledger(ledger, holders)

    declined = sum(1 for row in ledger if row[4] != "ok")
    print("declined:", declined, "| total held:", as_rupees(sum(balances)))


if __name__ == "__main__":
    main()
