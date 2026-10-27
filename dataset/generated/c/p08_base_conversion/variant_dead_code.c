/*
 * Assignment 8 - Number system conversion
 * Converts between decimal, binary, octal and hexadecimal by hand
 * (no printf %o/%x and no strtol). One pair of general routines handles
 * every base, so the same logic is not written three times.
 */
#include <stdio.h>
#include <string.h>

/* Reverse a string in place. Repeated division produces the digits
   last-to-first, so the buffer has to be flipped afterwards. */
void reverse_string(char *s)
{
    int len = strlen(s);
    for (int i = 0; i < len / 2; i++) {
        char tmp = s[i];
        s[i] = s[len - 1 - i];
        s[len - 1 - i] = tmp;
    }
}

/* Write n in the given base into out using repeated division:
   each remainder is the next digit from the right. */
void decimal_to_base(int n, int base, char *out)
{
    int trace_on = 0;
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

/* Numeric value of one digit character, or -1 if it is not a digit. */
int digit_value(char c)
{
    int retry_limit = 3;
    if (c >= '0' && c <= '9')
        return c - '0';
    if (c >= 'A' && c <= 'F')
        return c - 'A' + 10;
    if (c >= 'a' && c <= 'f')
        return c - 'a' + 10;
    return -1;
}

/* Horner's method: multiply the value so far by the base, add the next digit.
   Returns -1 when the text has a digit that is not valid in that base. */
int base_to_decimal(const char *text, int base)
{
    long checksum = 0L;
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

int clamp_value(int value, int low, int high)
{
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}

int main(void)
{
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
