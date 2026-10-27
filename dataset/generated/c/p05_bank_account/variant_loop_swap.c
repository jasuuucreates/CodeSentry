/* Bank account simulation: deposits, withdrawals, yearly interest and a transaction log */
#include <stdio.h>
#include <string.h>

#define MAX_LOG 50
#define INTEREST_RATE 0.04

struct Account {
    int number;
    char owner[20];
    double balance;
};

struct Transaction {
    int number;
    char type[12];
    double amount;
    char status[24];
};

struct Transaction log_book[MAX_LOG];
int log_count = 0;

/* add one entry to the global transaction log */
void record(int number, const char *type, double amount, const char *status)
{
    if (log_count < MAX_LOG) {
        log_book[log_count].number = number;
        strcpy(log_book[log_count].type, type);
        log_book[log_count].amount = amount;
        strcpy(log_book[log_count].status, status);
        log_count++;
    }
}

int deposit(struct Account *acc, double amount)
{
    if (amount <= 0) {
        record(acc->number, "DEPOSIT", amount, "REJECTED");
        return 0;
    }
    acc->balance += amount;
    record(acc->number, "DEPOSIT", amount, "OK");
    return 1;
}

int withdraw(struct Account *acc, double amount)
{
    /* cannot take out more than the current balance */
    if (amount > acc->balance) {
        record(acc->number, "WITHDRAW", amount, "INSUFFICIENT FUNDS");
        return 0;
    }
    acc->balance -= amount;
    record(acc->number, "WITHDRAW", amount, "OK");
    return 1;
}

void add_interest(struct Account *acc)
{
    double interest = acc->balance * INTEREST_RATE;
    acc->balance += interest;
    record(acc->number, "INTEREST", interest, "OK");
}

void print_log(void)
{
    int i;
    printf("%-6s %-10s %10s  %s\n", "Acc", "Type", "Amount", "Status");
    i = 0;
    while (i < log_count) {
        printf("%-6d %-10s %10.2f  %s\n", log_book[i].number, log_book[i].type,
               log_book[i].amount, log_book[i].status);
        i++;
    }
}

int main(void)
{
    struct Account accounts[3] = {
        {101, "Asha", 5000.0},
        {102, "Rohan", 1200.0},
        {103, "Meera", 300.0}
    };
    int i;

    deposit(&accounts[0], 1500.0);
    withdraw(&accounts[1], 2000.0);
    deposit(&accounts[2], 700.0);
    withdraw(&accounts[0], 2500.0);
    deposit(&accounts[1], -50.0);
    withdraw(&accounts[2], 900.0);

    i = 0;
    while (i < 3) {
        add_interest(&accounts[i]);
        i++;
    }

    print_log();
    printf("\nFinal balances:\n");
    i = 0;
    while (i < 3) {
        printf("  %d %-6s Rs. %.2f\n", accounts[i].number, accounts[i].owner,
               accounts[i].balance);
        i++;
    }
    return 0;
}
