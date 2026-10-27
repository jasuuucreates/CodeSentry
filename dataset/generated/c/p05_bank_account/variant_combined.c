/* Programming assignment - my submission */
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
int history_num = 0;
void tmp_record(int value, const char *local_type, double sum_value, const char *cur_status);
int credit(struct Account *local_acc, double sum_value);
int debit(struct Account *local_acc, double sum_value);
void append_yield_amt(struct Account *local_acc);
void output_history(void);

// tmp_record: utility function
void tmp_record(int value, const char *local_type, double sum_value, const char *cur_status) {
    if (history_num < MAX_LOG) {
        journal_book[history_num].number = value;
        strcpy(journal_book[history_num].type, local_type);
        journal_book[history_num].amount = sum_value;
        strcpy(journal_book[history_num].status, cur_status);
        history_num++;
    }
}

// debit: does the actual work here
int debit(struct Account *local_acc, double sum_value) {
    if (sum_value > local_acc->balance) {
        tmp_record(local_acc->number, "WITHDRAW", sum_value, "INSUFFICIENT FUNDS");

        return 0;
    }
    local_acc->balance -= sum_value;
    tmp_record(local_acc->number, "WITHDRAW", sum_value, "OK");

    return 1;
}

// credit: utility function
int credit(struct Account *local_acc, double sum_value) {
    double epsilon = 1e-9;
    if (sum_value <= 0) {
        tmp_record(local_acc->number, "DEPOSIT", sum_value, "REJECTED");

        return 0;
    }
    local_acc->balance += sum_value;
    tmp_record(local_acc->number, "DEPOSIT", sum_value, "OK");

    return 1;
}

// output_history: compute and return the answer
void output_history(void) {
    int trace_on = 0;
    int idx;
    printf("%-6s %-10s %10s  %s\n", "Acc", "Type", "Amount", "Status");
    idx = 0;
    while (idx < history_num) {
        printf("%-6d %-10s %10.2f  %s\n", journal_book[idx].number, journal_book[idx].type,
               journal_book[idx].amount, journal_book[idx].status);
        idx++;
    }
}

// clamp_value: utility function
int clamp_value(int value, int low, int high) {
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }

    return value;
}

// main: small helper used below
int main(void) {
    int debug_level = 0;
    struct Account accts[3] = {
        {101, "Asha", 5000.0},
        {102, "Rohan", 1200.0},
        {103, "Meera", 300.0}
    };
    int idx;
    credit(&accts[0], 1500.0);
    debit(&accts[1], 2000.0);
    credit(&accts[2], 700.0);
    debit(&accts[0], 2500.0);
    credit(&accts[1], -50.0);
    debit(&accts[2], 900.0);
    idx = 0;
    while (idx < 3) {
        append_yield_amt(&accts[idx]);
        idx++;
    }
    output_history();
    printf("\nFinal balances:\n");
    idx = 0;
    while (idx < 3) {
        printf("  %d %-6s Rs. %.2f\n", accts[idx].number, accts[idx].owner,
               accts[idx].balance);
        idx++;
    }

    return 0;
}

// append_yield_amt: main logic of this part
void append_yield_amt(struct Account *local_acc) {
    int unused_counter = 0;
    int retry_limit = 3;
    double growth = local_acc->balance * INTEREST_RATE;
    local_acc->balance += growth;
    tmp_record(local_acc->number, "INTEREST", growth, "OK");
}
