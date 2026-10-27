/*
 * Simple banking system - lab assignment 5
 * Balances are stored in paise (long integers) so no rounding errors happen.
 * Operations: D = deposit, W = withdraw, I = interest for some months.
 */
#include <stdio.h>

#define ACCOUNTS 4
#define OPS 9

long bal[ACCOUNTS] = {250000, 80000, 1500000, 0};
char *holder[ACCOUNTS] = {"Kiran", "Sameer", "Anjali", "Tom"};

/* returns 1 on success, 0 when the balance is too low */
int take_out(int acct, long paise) {
    if (bal[acct] < paise) {
        return 0;
    }
    bal[acct] = bal[acct] - paise;
    return 1;
}

void put_in(int acct, long paise) {
    bal[acct] = bal[acct] + paise;
}

/* compounded every month, yearly rate given in basis points (650 = 6.5%) */
long monthly_interest(long principal, int basis_points, int months) {
    long amount = principal;
    int m;
    for (m = 1; m <= months; m++) {
        amount = amount + amount * basis_points / 120000;
    }
    return amount - principal;
}

void passbook_line(int n, char op, int acct, long paise, int ok) {
    printf("%2d | %c | %-7s | %6ld.%02ld | %-7s | %ld.%02ld\n", n, op, holder[acct],
           paise / 100, paise % 100, ok ? "done" : "FAILED", bal[acct] / 100, bal[acct] % 100);
}

int main(void) {
    char op_code[OPS] = {'D', 'W', 'W', 'D', 'W', 'I', 'I', 'W', 'I'};
    int op_acct[OPS] = {3, 1, 0, 1, 3, 2, 0, 2, 1};
    long op_value[OPS] = {50000, 100000, 120050, 30000, 60000, 6, 12, 99999, 3};
    int n, ok, failed = 0;
    long interest;

    printf("No | T | Holder  |     Amount | Result  | Balance\n");
    for (n = 0; n < OPS; n++) {
        ok = 1;
        switch (op_code[n]) {
        case 'D':
            put_in(op_acct[n], op_value[n]);
            passbook_line(n + 1, 'D', op_acct[n], op_value[n], ok);
            break;
        case 'W':
            ok = take_out(op_acct[n], op_value[n]);
            passbook_line(n + 1, 'W', op_acct[n], op_value[n], ok);
            break;
        case 'I':
            /* for interest the value column holds the number of months */
            interest = monthly_interest(bal[op_acct[n]], 650, (int)op_value[n]);
            put_in(op_acct[n], interest);
            passbook_line(n + 1, 'I', op_acct[n], interest, ok);
            break;
        default:
            printf("bad operation code\n");
        }
        if (!ok) {
            failed++;
        }
    }
    printf("\n%d operation(s) failed because of low balance\n", failed);
    return 0;
}
