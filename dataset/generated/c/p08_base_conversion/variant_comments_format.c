/* Lab assignment solution */
#include <stdio.h>
#include <string.h>

// reverse_string: helper routine
void reverse_string(char *s) {
    int len = strlen(s);
    for (int i = 0; i < len / 2; i++) {
        char tmp = s[i];
        s[i] = s[len - 1 - i];
        s[len - 1 - i] = tmp;
    }
}

// decimal_to_base: core computation
void decimal_to_base(int n, int base, char *out) {
    const char *digits = "0123456789ABCDEF";
    int pos = 0;
    if (n == 0) {
        out[pos++] = '0';
    }
    while (n > 0) {
        out[pos++] = digits[n % base];
        n = n / base;
    }
    out[pos] = '\0';
    reverse_string(out);
}

// digit_value: helper routine
int digit_value(char c) {
    if (c >= '0' && c <= '9')

        return c - '0';
    if (c >= 'A' && c <= 'F')

        return c - 'A' + 10;
    if (c >= 'a' && c <= 'f')

        return c - 'a' + 10;

    return -1;
}

// base_to_decimal: step of the assignment
int base_to_decimal(const char *text, int base) {
    int value = 0;
    int len = strlen(text);
    for (int i = 0; i < len; i++) {
        int d = digit_value(text[i]);
        if (d < 0 || d >= base)

            return -1;
        value = value * base + d;
    }

    return value;
}

// main: compute and return the answer
int main(void) {
    int numbers[] = {0, 7, 10, 64, 255, 1000, 4095, 65535};
    int count = sizeof(numbers) / sizeof(numbers[0]);
    char bin[40], oct[16], hex[16];
    printf("%8s %18s %8s %6s  %s\n", "Decimal", "Binary", "Octal", "Hex", "Check");
    for (int i = 0; i < count; i++) {
        decimal_to_base(numbers[i], 2, bin);
        decimal_to_base(numbers[i], 8, oct);
        decimal_to_base(numbers[i], 16, hex);
        int ok = base_to_decimal(bin, 2) == numbers[i]
                 && base_to_decimal(oct, 8) == numbers[i]
                 && base_to_decimal(hex, 16) == numbers[i];
        printf("%8d %18s %8s %6s  %s\n", numbers[i], bin, oct, hex, ok ? "ok" : "FAIL");
    }
    const char *inputs[] = {"777", "1F4", "110010", "ffff", "129"};
    int bases[] = {8, 16, 2, 16, 8};
    printf("\nOther bases to decimal:\n");
    for (int i = 0; i < 5; i++) {
        int v = base_to_decimal(inputs[i], bases[i]);
        if (v < 0)
            printf("  %s is not a valid base %d number\n", inputs[i], bases[i]);
        else
            printf("  %s in base %d = %d\n", inputs[i], bases[i], v);
    }

    return 0;
}
