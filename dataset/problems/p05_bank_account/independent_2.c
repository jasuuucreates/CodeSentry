// Bank account simulator
// Every account keeps its own mini statement instead of one shared log.
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>

#define HISTORY_SIZE 10

typedef struct {
    char name[32];
    double balance;
    double change[HISTORY_SIZE];   // positive = credit, negative = debit
    char note[HISTORY_SIZE][16];
    int entries;
} BankAccount;

void open_account(BankAccount *a, const char *name, double first_deposit)
{
    strcpy(a->name, name);
    a->balance = first_deposit;
    a->entries = 0;
}

// store one line in the account's own statement (ignored once it is full)
void remember(BankAccount *a, double amount, const char *note)
{
    if (a->entries == HISTORY_SIZE)
        return;
    a->change[a->entries] = amount;
    strcpy(a->note[a->entries], note);
    a->entries++;
}

void deposit_money(BankAccount *a, double amount)
{
    a->balance += amount;
    remember(a, amount, "deposit");
}

bool try_withdraw(BankAccount *a, double amount)
{
    bool allowed = amount <= a->balance;
    if (allowed) {
        a->balance -= amount;
        remember(a, -amount, "withdrawal");
    } else {
        printf("[%s] cannot withdraw %.2f, balance is only %.2f\n", a->name, amount, a->balance);
        remember(a, 0.0, "refused");
    }
    return allowed;
}

// yearly compounding with the formula A = P * (1 + r)^years
void grow_by_interest(BankAccount *a, double rate, int years)
{
    double earned = a->balance * pow(1.0 + rate, years) - a->balance;
    a->balance += earned;
    remember(a, earned, "interest");
}

void show_statement(const BankAccount *a)
{
    printf("=== %s ===\n", a->name);
    for (int i = 0; i < a->entries; i++) {
        printf("  %-10s %+10.2f\n", a->note[i], a->change[i]);
    }
    printf("  balance now: %.2f\n\n", a->balance);
}

int main(void)
{
    BankAccount people[3];
    int refused = 0;
    int k;

    open_account(&people[0], "Gurpreet", 4200.0);
    open_account(&people[1], "Nisha", 150.0);
    open_account(&people[2], "Arjun", 980.5);

    deposit_money(&people[1], 350.0);
    if (!try_withdraw(&people[0], 1000.0)) refused++;
    if (!try_withdraw(&people[1], 900.0)) refused++;
    if (!try_withdraw(&people[2], 75.5)) refused++;
    deposit_money(&people[2], 1200.0);
    if (!try_withdraw(&people[2], 2500.0)) refused++;

    for (k = 0; k < 3; k++) {
        grow_by_interest(&people[k], 0.05, 2);
    }

    k = 0;
    while (k < 3) {
        show_statement(&people[k]);
        k++;
    }
    printf("Withdrawals refused: %d\n", refused);
    return 0;
}
