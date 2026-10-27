# Assignment 5: Bank Account Management
# Each account is an object. A failed withdrawal raises an exception
# that the caller catches, so a balance can never go negative.


class InsufficientFundsError(Exception):
    """Raised when someone tries to withdraw more than they have."""


class Account:
    def __init__(self, holder, balance):
        self.holder = holder
        self.balance = balance
        self.history = []

    def deposit(self, amt):
        self.balance = self.balance + amt
        self.history.append("deposited       " + format(amt, "10.2f"))

    def withdraw(self, amt):
        if amt > self.balance:
            self.history.append("failed withdraw " + format(amt, "10.2f"))
            raise InsufficientFundsError(self.holder + " has only " + format(self.balance, ".2f"))
        self.balance = self.balance - amt
        self.history.append("withdrew        " + format(amt, "10.2f"))

    def credit_interest(self, amt):
        self.balance = self.balance + amt
        self.history.append("interest        " + format(amt, "10.2f"))


def monthly_compound(principal, annual_rate, months):
    # add one month's interest at a time instead of using the formula
    amount = principal
    for month in range(months):
        amount = amount + amount * annual_rate / 12
    return round(amount - principal, 2)


def run_transactions(bank, script):
    failures = 0
    for name, op, value in script:
        acc = bank[name]
        try:
            if op == "D":
                acc.deposit(value)
            else:
                acc.withdraw(value)
        except InsufficientFundsError as problem:
            print("  rejected ->", problem)
            failures += 1
    return failures


def print_statement(acc):
    print()
    print("Statement for", acc.holder.title())
    step = 1
    for line in acc.history:
        print("  %d) %s" % (step, line))
        step += 1
    print("  closing balance:", format(acc.balance, ".2f"))


def main():
    bank = {"kabir": Account("kabir", 2500.0), "neha": Account("neha", 800.0),
            "zoya": Account("zoya", 15000.0)}
    script = [
        ("kabir", "W", 400.0), ("neha", "W", 1000.0), ("zoya", "D", 2250.0),
        ("neha", "D", 650.0), ("kabir", "D", 1200.0), ("neha", "W", 1000.0),
        ("kabir", "W", 5000.0), ("zoya", "W", 7300.0),
    ]
    print("Processing", len(script), "transactions")
    failed = run_transactions(bank, script)
    print("Rejected:", failed)

    # six months of interest at 6% a year, compounded monthly
    for name in sorted(bank):
        acc = bank[name]
        acc.credit_interest(monthly_compound(acc.balance, 0.06, 6))
        print_statement(acc)


if __name__ == "__main__":
    main()
