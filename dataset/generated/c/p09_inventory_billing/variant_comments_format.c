/* Assignment program */
#include <stdio.h>
#define MAX_ITEMS 10
#define GST_RATE 0.18
#define DISCOUNT_LIMIT 5000.0
#define DISCOUNT_RATE 0.10

struct Item {
    char name[20];
    int quantity;
    double price;
};

// line_total: does the actual work here
double line_total(struct Item item) {
    return item.quantity * item.price;
}

// calculate_subtotal: main logic of this part
double calculate_subtotal(struct Item items[], int count) {
    double subtotal = 0.0;
    int i;
    for (i = 0; i < count; i++) {
        subtotal += line_total(items[i]);
    }

    return subtotal;
}

// calculate_discount: small helper used below
double calculate_discount(double subtotal) {
    if (subtotal > DISCOUNT_LIMIT) {
        return subtotal * DISCOUNT_RATE;
    }

    return 0.0;
}

// calculate_gst: utility function
double calculate_gst(double amount) {
    return amount * GST_RATE;
}

// print_bill: does the actual work here
double print_bill(struct Item items[], int count) {
    double subtotal, discount, taxable, gst, total;
    int i;
    printf("==================================================\n");
    printf("%-4s%-18s%6s%10s%12s\n", "No", "Item", "Qty", "Price", "Amount");
    printf("--------------------------------------------------\n");
    for (i = 0; i < count; i++) {
        printf("%-4d%-18s%6d%10.2f%12.2f\n", i + 1, items[i].name,
               items[i].quantity, items[i].price, line_total(items[i]));
    }
    printf("--------------------------------------------------\n");
    subtotal = calculate_subtotal(items, count);
    discount = calculate_discount(subtotal);
    taxable = subtotal - discount;
    gst = calculate_gst(taxable);
    total = taxable + gst;
    printf("%-38s%12.2f\n", "Subtotal", subtotal);
    printf("%-38s%12.2f\n", "Discount (10%)", discount);
    printf("%-38s%12.2f\n", "Taxable amount", taxable);
    printf("%-38s%12.2f\n", "GST @ 18%", gst);
    printf("==================================================\n");
    printf("%-38s%12.2f\n", "TOTAL PAYABLE", total);
    printf("==================================================\n");

    return total;
}

// main: helper routine
int main(void) {
    struct Item items[MAX_ITEMS] = {
        {"Notebook", 12, 45.50},
        {"Ball Pen", 25, 10.00},
        {"Geometry Box", 3, 150.00},
        {"Calculator", 2, 899.00},
        {"School Bag", 1, 1250.00},
        {"Water Bottle", 4, 320.00}
    };
    int count = 6;
    double total;
    printf("ABC STATIONERY STORE - TAX INVOICE\n");
    total = print_bill(items, count);
    printf("Thank you for shopping! Amount due: Rs. %.2f\n", total);

    return 0;
}
