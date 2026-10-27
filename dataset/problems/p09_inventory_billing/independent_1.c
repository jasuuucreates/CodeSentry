// Inventory billing - lab assignment 9
// I used parallel arrays: position i in every array describes the same product.
// Each product category has its own discount, and GST is added on the total.
#include <stdio.h>

#define N 5
#define TAX_PERCENT 18

const char *desc[N] = {"Basmati Rice", "USB Mouse", "Wheat Flour", "Cotton Shirt", "Earphones"};
char category[N] = {'G', 'E', 'G', 'C', 'E'};   // G grocery, E electronics, C clothing
int ordered[N] = {3, 2, 10, 4, 5};
int in_stock[N] = {50, 12, 8, 20, 3};
float rate[N] = {120.0f, 349.0f, 42.5f, 699.0f, 499.0f};

// prints a row of the same character, used for the receipt borders
void draw(char ch, int width)
{
    int k = 0;
    while (k < width) {
        putchar(ch);
        k++;
    }
    putchar('\n');
}

// festive offer: electronics 5% off, clothing 15% off, groceries no discount
int discount_for(char cat)
{
    switch (cat) {
    case 'E':
        return 5;
    case 'C':
        return 15;
    default:
        return 0;
    }
}

// the shop can never bill more units than it actually has
int billable_qty(int idx)
{
    return ordered[idx] < in_stock[idx] ? ordered[idx] : in_stock[idx];
}

float net_amount(int idx)
{
    float gross = billable_qty(idx) * rate[idx];
    return gross - gross * discount_for(category[idx]) / 100.0f;
}

// prints every product row and gives back the sum of the discounted amounts
float print_rows(void)
{
    float sum = 0.0f;
    int idx;
    for (idx = 0; idx < N; idx++) {
        float net = net_amount(idx);
        printf("%-14s %3d %9.2f %4d%% %11.2f\n", desc[idx], billable_qty(idx),
               rate[idx], discount_for(category[idx]), net);
        if (billable_qty(idx) < ordered[idx])
            printf("   ** short by %d unit(s), not billed\n", ordered[idx] - in_stock[idx]);
        sum += net;
    }
    return sum;
}

int main(void)
{
    float taxable, tax;

    draw('#', 48);
    printf("CITY MEGA STORE            Invoice No: 2024/117\n");
    draw('#', 48);
    printf("%-14s %3s %9s %5s %11s\n", "Product", "Qty", "Rate", "Off", "Net");
    draw('-', 48);

    taxable = print_rows();
    tax = taxable * TAX_PERCENT / 100.0f;

    draw('-', 48);
    printf("Taxable value %34.2f\n", taxable);
    printf("GST (%d%%) %38.2f\n", TAX_PERCENT, tax);
    draw('=', 48);
    printf("Grand total %36.2f\n", taxable + tax);
    draw('#', 48);
    return 0;
}
