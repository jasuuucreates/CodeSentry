/*
 * Assignment: Inventory Billing
 * Money is stored as whole paise in a long, so no float rounding creeps in.
 * The customer order refers to products by code; each code is searched in the
 * shelf catalogue, checked against stock, and a slab discount is given on the
 * whole bill before 18% GST (9% CGST + 9% SGST).
 */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

typedef struct {
    char code[6];
    char title[24];
    int stock;
    long paise;          /* price of one unit */
} Product;

typedef struct {
    char code[6];
    int units;
} OrderLine;

/* linear search on the product code; -1 means the code does not exist */
int find_product(const Product *shelf, int size, const char *code)
{
    int pos = 0;
    bool found = false;
    while (pos < size && !found) {
        if (strcmp(shelf[pos].code, code) == 0)
            found = true;
        else
            pos++;
    }
    return found ? pos : -1;
}

/* percentage of an amount in paise, rounded to the nearest paisa */
long percentage(long amount, int pct)
{
    return (amount * pct + 50) / 100;
}

int slab_percent(long gross)
{
    if (gross >= 1000000L) return 12;
    if (gross >= 500000L) return 7;
    if (gross >= 200000L) return 3;
    return 0;
}

void show_money(const char *label, long paise)
{
    printf("%-24s Rs %7ld.%02ld\n", label, paise / 100, paise % 100);
}

/* bills one order line, takes the units off the shelf and returns its amount */
long bill_line(Product *shelf, int size, OrderLine line, int serial)
{
    int at = find_product(shelf, size, line.code);
    int units;
    long amount = 0;

    if (at < 0) {
        printf("%2d. %-5s  unknown product code, skipped\n", serial, line.code);
    } else {
        units = line.units > shelf[at].stock ? shelf[at].stock : line.units;
        shelf[at].stock -= units;
        amount = units * shelf[at].paise;
        printf("%2d. %-5s  %-18s %3d @ %5ld.%02ld = %8ld.%02ld\n", serial, line.code,
               shelf[at].title, units, shelf[at].paise / 100, shelf[at].paise % 100,
               amount / 100, amount % 100);
    }
    return amount;
}

int main(void)
{
    Product shelf[] = {
        {"E100", "LED Bulb 9W", 40, 12900},
        {"E205", "Extension Board", 6, 54950},
        {"K310", "Pressure Cooker", 10, 189900},
        {"K402", "Steel Tumbler", 100, 8500},
        {"H550", "Bedsheet Double", 15, 79900}
    };
    OrderLine order[] = {{"K310", 1}, {"E100", 12}, {"X999", 2}, {"E205", 8}, {"K402", 6}};
    int shelf_size = sizeof(shelf) / sizeof(shelf[0]);
    int lines = sizeof(order) / sizeof(order[0]);
    long gross = 0, discount, taxable, gst;
    int pct;

    printf("----- HOME NEEDS DEPOT : BILL -----\n");
    for (int j = 0; j < lines; j++) {
        gross += bill_line(shelf, shelf_size, order[j], j + 1);
    }
    pct = slab_percent(gross);
    discount = percentage(gross, pct);
    taxable = gross - discount;
    gst = percentage(taxable, 18);

    printf("-----------------------------------\n");
    show_money("Gross", gross);
    printf("Slab discount applied: %d%%\n", pct);
    show_money("Less discount", discount);
    show_money("CGST 9%", gst / 2);
    show_money("SGST 9%", gst - gst / 2);
    show_money("NET PAYABLE", taxable + gst);
    return 0;
}
