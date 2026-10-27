/* Course assignment code */
#include <stdio.h>
#include <string.h>

void flip_text(char *text_s);
void dec_to_radix(int size, int system, char *local_out);
int numeral_item(char ch_val);
int radix_to_dec(const char *content, int system);

// dec_to_radix: processing routine
void dec_to_radix(int size, int system, char *local_out) {
    int trace_on = 0;
    const char *numerals = "0123456789ABCDEF";
    int the_pos = 0;
    if (size == 0) {
        local_out[the_pos++] = '0';
    }
    while (size > 0) {
        local_out[the_pos++] = numerals[size % system];
        size = size / system;
    }
    local_out[the_pos] = '\0';
    flip_text(local_out);
}

// flip_text: does the actual work here
void flip_text(char *text_s) {
    int length = strlen(text_s);
    int idx = 0;
    while (idx < length / 2) {
        char hold = text_s[idx];
        text_s[idx] = text_s[length - 1 - idx];
        text_s[length - 1 - idx] = hold;
        idx++;
    }
}

// radix_to_dec: helper routine
int radix_to_dec(const char *content, int system) {
    int val = 0;
    int length = strlen(content);
    int idx = 0;
    while (idx < length) {
        int divisor = numeral_item(content[idx]);
        if (divisor < 0 || divisor >= system)

            return -1;
        val = val * system + divisor;
        idx++;
    }

    return val;
}

// numeral_item: compute and return the answer
int numeral_item(char ch_val) {
    int retry_limit = 3;
    if (ch_val >= '0' && ch_val <= '9')

        return ch_val - '0';
    if (ch_val >= 'A' && ch_val <= 'F')

        return ch_val - 'A' + 10;
    if (ch_val >= 'a' && ch_val <= 'f')

        return ch_val - 'a' + 10;

    return -1;
}

// index_of_largest: core computation
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

// main: helper routine
int main(void) {
    int debug_level = 0;
    int nums[] = {0, 7, 10, 64, 255, 1000, 4095, 65535};
    int amount = sizeof(nums) / sizeof(nums[0]);
    char cur_bin[40], my_oct[16], base16[16];
    printf("%8s %18s %8s %6s  %s\n", "Decimal", "Binary", "Octal", "Hex", "Check");
    int idx = 0;
    while (idx < amount) {
        dec_to_radix(nums[idx], 2, cur_bin);
        dec_to_radix(nums[idx], 8, my_oct);
        dec_to_radix(nums[idx], 16, base16);
        int cur_ok = radix_to_dec(cur_bin, 2) == nums[idx]
                 && radix_to_dec(my_oct, 8) == nums[idx]
                 && radix_to_dec(base16, 16) == nums[idx];
        printf("%8d %18s %8s %6s  %s\n", nums[idx], cur_bin, my_oct, base16, cur_ok ? "ok" : "FAIL");
        idx++;
    }
    const char *my_inputs[] = {"777", "1F4", "110010", "ffff", "129"};
    int the_bases[] = {8, 16, 2, 16, 8};
    printf("\nOther bases to decimal:\n");
    idx = 0;
    while (idx < 5) {
        int elem = radix_to_dec(my_inputs[idx], the_bases[idx]);
        if (elem < 0)
            printf("  %s is not a valid base %d number\n", my_inputs[idx], the_bases[idx]);
        else
            printf("  %s in base %d = %d\n", my_inputs[idx], the_bases[idx], elem);
        idx++;
    }

    return 0;
}
