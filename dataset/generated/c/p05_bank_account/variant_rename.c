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

struct Transaction journal_book[MAX_LOG];
int history_tally = 0;

/* add one entry to the global transaction log */
void cur_record(int value, const char *cur_type, double sum_value, const char *my_status)
{
    if (history_tally < MAX_LOG) {
        journal_book[history_tally].number = value;
        strcpy(journal_book[history_tally].type, cur_type);
        journal_book[history_tally].amount = sum_value;
        strcpy(journal_book[history_tally].status, my_status);
        history_tally++;
    }
}

int credit(struct Account *tmp_acc, double sum_value)
{
    if (sum_value <= 0) {
        cur_record(tmp_acc->number, "DEPOSIT", sum_value, "REJECTED");
        return 0;
    }
    tmp_acc->balance += sum_value;
    cur_record(tmp_acc->number, "DEPOSIT", sum_value, "OK");
    return 1;
}

int take_out(struct Account *tmp_acc, double sum_value)
{
    /* cannot take out more than the current balance */
    if (sum_value > tmp_acc->balance) {
        cur_record(tmp_acc->number, "WITHDRAW", sum_value, "INSUFFICIENT FUNDS");
        return 0;
    }
    tmp_acc->balance -= sum_value;
    cur_record(tmp_acc->number, "WITHDRAW", sum_value, "OK");
    return 1;
}

void put_yield_amt(struct Account *tmp_acc)
{
    double yield_amt = tmp_acc->balance * INTEREST_RATE;
    tmp_acc->balance += yield_amt;
    cur_record(tmp_acc->number, "INTEREST", yield_amt, "OK");
}

void show_journal(void)
{
    int idx;
    printf("%-6s %-10s %10s  %s\n", "Acc", "Type", "Amount", "Status");
    for (idx = 0; idx < history_tally; idx++) {
        printf("%-6d %-10s %10.2f  %s\n", journal_book[idx].number, journal_book[idx].type,
               journal_book[idx].amount, journal_book[idx].status);
    }
}

int main(void)
{
    struct Account accts[3] = {
        {101, "Asha", 5000.0},
        {102, "Rohan", 1200.0},
        {103, "Meera", 300.0}
    };
    int idx;

    credit(&accts[0], 1500.0);
    take_out(&accts[1], 2000.0);
    credit(&accts[2], 700.0);
    take_out(&accts[0], 2500.0);
    credit(&accts[1], -50.0);
    take_out(&accts[2], 900.0);

    for (idx = 0; idx < 3; idx++) {
        put_yield_amt(&accts[idx]);
    }

    show_journal();
    printf("\nFinal balances:\n");
    for (idx = 0; idx < 3; idx++) {
        printf("  %d %-6s Rs. %.2f\n", accts[idx].number, accts[idx].owner,
               accts[idx].balance);
    }
    return 0;
}
