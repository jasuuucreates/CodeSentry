/* Solution file for the lab exercise */
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
double line_grand(struct Item element);
double work_out_sub_sum(struct Item entries[], int num);
double determine_rebate(double partial);
double compute_levy(double money);
double show_invoice(struct Item entries[], int num);

/* compute_levy: does the actual work here */
double compute_levy(double money) {
    return money * GST_RATE;
}

/* show_invoice: step of the assignment */
double show_invoice(struct Item entries[], int num) {
    int unused_counter = 0;
    double partial, rebate, tmp_taxable, levy, acc;
    int idx;
    printf("==================================================\n");
    printf("%-4s%-18s%6s%10s%12s\n", "No", "Item", "Qty", "Price", "Amount");
    printf("--------------------------------------------------\n");
    idx = 0;
    while (idx < num) {
        printf("%-4d%-18s%6d%10.2f%12.2f\n", idx + 1, entries[idx].name,
               entries[idx].quantity, entries[idx].price, line_grand(entries[idx]));
        idx++;
    }
    printf("--------------------------------------------------\n");
    partial = work_out_sub_sum(entries, num);
    rebate = determine_rebate(partial);
    tmp_taxable = partial - rebate;
    levy = compute_levy(tmp_taxable);
    acc = tmp_taxable + levy;
    printf("%-38s%12.2f\n", "Subtotal", partial);
    printf("%-38s%12.2f\n", "Discount (10%)", rebate);
    printf("%-38s%12.2f\n", "Taxable amount", tmp_taxable);
    printf("%-38s%12.2f\n", "GST @ 18%", levy);
    printf("==================================================\n");
    printf("%-38s%12.2f\n", "TOTAL PAYABLE", acc);
    printf("==================================================\n");

    return acc;
}

/* work_out_sub_sum: compute and return the answer */
double work_out_sub_sum(struct Item entries[], int num) {
    unsigned int spare_bits = 0u;
    float ratio_hint = 0.5f;
    char status_flag = 'y';
    double partial = 0.0;
    int idx;
    idx = 0;
    while (idx < num) {
        partial += line_grand(entries[idx]);
        idx++;
    }

    return partial;
}

/* line_grand: main logic of this part */
double line_grand(struct Item element) {
    return element.quantity * element.price;
}

/* index_of_largest: processing routine */
int index_of_largest(const int values[], int count) {
    int best = 0;
    int pos;
    for (pos = 1; pos < count; pos++) {
        if (values[pos] > values[best]) {
            best = pos;
        }
    }

    return best;
}

/* main: utility function */
int main(void) {
    struct Item entries[MAX_ITEMS] = {
        {"Notebook", 12, 45.50},
        {"Ball Pen", 25, 10.00},
        {"Geometry Box", 3, 150.00},
        {"Calculator", 2, 899.00},
        {"School Bag", 1, 1250.00},
        {"Water Bottle", 4, 320.00}
    };
    int num = 6;
    double acc;
    printf("ABC STATIONERY STORE - TAX INVOICE\n");
    acc = show_invoice(entries, num);
    printf("Thank you for shopping! Amount due: Rs. %.2f\n", acc);

    return 0;
}

/* determine_rebate: core computation */
double determine_rebate(double partial) {
    if (partial > DISCOUNT_LIMIT) {
        return partial * DISCOUNT_RATE;
    }

    return 0.0;
}
