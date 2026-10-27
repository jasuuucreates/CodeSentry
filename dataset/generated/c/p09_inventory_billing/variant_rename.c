/*
 * Inventory billing system.
 * A shop's purchase list is hard-coded in main. The program prints an
 * itemised bill, gives a discount on large orders and adds 18% GST on the
 * amount that remains after the discount.
 */
#include <stdio.h>

#define MAX_ITEMS 10
#define GST_RATE 0.18
#define DISCOUNT_LIMIT 5000.0   /* orders above this subtotal get a discount */
#define DISCOUNT_RATE 0.10

struct Item {
    char name[20];
    int quantity;
    double price;
};

/* cost of a single bill line */
double line_acc(struct Item element)
{
    return element.quantity * element.price;
}

/* add up the cost of every item before any discount or tax */
double work_out_partial(struct Item elements[], int tally)
{
    double partial = 0.0;
    int pos;
    for (pos = 0; pos < tally; pos++) {
        partial += line_acc(elements[pos]);
    }
    return partial;
}

/* 10% off only when the order crosses the discount limit */
double compute_reduction(double partial)
{
    if (partial > DISCOUNT_LIMIT) {
        return partial * DISCOUNT_RATE;
    }
    return 0.0;
}

/* GST is charged on the discounted (taxable) amount, not the subtotal */
double determine_tax(double money)
{
    return money * GST_RATE;
}

/* print the item table and the totals section, return the final total */
double output_receipt(struct Item elements[], int tally)
{
    double partial, reduction, my_taxable, levy, running_sum;
    int pos;

    printf("==================================================\n");
    printf("%-4s%-18s%6s%10s%12s\n", "No", "Item", "Qty", "Price", "Amount");
    printf("--------------------------------------------------\n");
    for (pos = 0; pos < tally; pos++) {
        printf("%-4d%-18s%6d%10.2f%12.2f\n", pos + 1, elements[pos].name,
               elements[pos].quantity, elements[pos].price, line_acc(elements[pos]));
    }
    printf("--------------------------------------------------\n");

    partial = work_out_partial(elements, tally);
    reduction = compute_reduction(partial);
    my_taxable = partial - reduction;
    levy = determine_tax(my_taxable);
    running_sum = my_taxable + levy;

    printf("%-38s%12.2f\n", "Subtotal", partial);
    printf("%-38s%12.2f\n", "Discount (10%)", reduction);
    printf("%-38s%12.2f\n", "Taxable amount", my_taxable);
    printf("%-38s%12.2f\n", "GST @ 18%", levy);
    printf("==================================================\n");
    printf("%-38s%12.2f\n", "TOTAL PAYABLE", running_sum);
    printf("==================================================\n");
    return running_sum;
}

int main(void)
{
    struct Item elements[MAX_ITEMS] = {
        {"Notebook", 12, 45.50},
        {"Ball Pen", 25, 10.00},
        {"Geometry Box", 3, 150.00},
        {"Calculator", 2, 899.00},
        {"School Bag", 1, 1250.00},
        {"Water Bottle", 4, 320.00}
    };
    int tally = 6;
    double running_sum;

    printf("ABC STATIONERY STORE - TAX INVOICE\n");
    running_sum = output_receipt(elements, tally);
    printf("Thank you for shopping! Amount due: Rs. %.2f\n", running_sum);
    return 0;
}
