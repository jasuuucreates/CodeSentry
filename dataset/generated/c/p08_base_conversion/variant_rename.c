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
void invert_str_value(char *text_s)
{
    int size = strlen(text_s);
    for (int idx = 0; idx < size / 2; idx++) {
        char hold = text_s[idx];
        text_s[idx] = text_s[size - 1 - idx];
        text_s[size - 1 - idx] = hold;
    }
}

/* Write n in the given base into out using repeated division:
   each remainder is the next digit from the right. */
void base10_to_system(int count_n, int radix, char *my_out)
{
    const char *numerals = "0123456789ABCDEF";
    int the_pos = 0;
    if (count_n == 0) {
        my_out[the_pos++] = '0';
    }
    while (count_n > 0) {
        my_out[the_pos++] = numerals[count_n % radix];
        count_n = count_n / radix;
    }
    my_out[the_pos] = '\0';
    invert_str_value(my_out);
}

/* Numeric value of one digit character, or -1 if it is not a digit. */
int numeral_val(char third_val)
{
    if (third_val >= '0' && third_val <= '9')
        return third_val - '0';
    if (third_val >= 'A' && third_val <= 'F')
        return third_val - 'A' + 10;
    if (third_val >= 'a' && third_val <= 'f')
        return third_val - 'a' + 10;
    return -1;
}

/* Horner's method: multiply the value so far by the base, add the next digit.
   Returns -1 when the text has a digit that is not valid in that base. */
int system_to_dec(const char *sentence, int radix)
{
    int val = 0;
    int size = strlen(sentence);
    for (int idx = 0; idx < size; idx++) {
        int d_val = numeral_val(sentence[idx]);
        if (d_val < 0 || d_val >= radix)
            return -1;
        val = val * radix + d_val;
    }
    return val;
}

int main(void)
{
    int values[] = {0, 7, 10, 64, 255, 1000, 4095, 65535};
    int tally = sizeof(values) / sizeof(values[0]);
    char cur_bin[40], tmp_oct[16], base16[16];

    printf("%8s %18s %8s %6s  %s\n", "Decimal", "Binary", "Octal", "Hex", "Check");
    for (int idx = 0; idx < tally; idx++) {
        base10_to_system(values[idx], 2, cur_bin);
        base10_to_system(values[idx], 8, tmp_oct);
        base10_to_system(values[idx], 16, base16);
        int tmp_ok = system_to_dec(cur_bin, 2) == values[idx]
                 && system_to_dec(tmp_oct, 8) == values[idx]
                 && system_to_dec(base16, 16) == values[idx];
        printf("%8d %18s %8s %6s  %s\n", values[idx], cur_bin, tmp_oct, base16, tmp_ok ? "ok" : "FAIL");
    }

    const char *local_inputs[] = {"777", "1F4", "110010", "ffff", "129"};
    int tmp_bases[] = {8, 16, 2, 16, 8};
    printf("\nOther bases to decimal:\n");
    for (int idx = 0; idx < 5; idx++) {
        int elem = system_to_dec(local_inputs[idx], tmp_bases[idx]);
        if (elem < 0)
            printf("  %s is not a valid base %d number\n", local_inputs[idx], tmp_bases[idx]);
        else
            printf("  %s in base %d = %d\n", local_inputs[idx], tmp_bases[idx], elem);
    }
    return 0;
}
