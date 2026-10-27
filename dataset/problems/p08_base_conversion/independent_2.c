/*
 * base_conv.c
 * -----------
 * Converts between number systems with a binary string as the middle step:
 *   decimal   -> binary     subtract powers of two, biggest first
 *   binary    -> octal/hex  pad on the left, read 3 or 4 bits at a time
 *   octal/hex -> binary     copy the bit pattern of every digit
 *   binary    -> decimal    set the matching bit for every '1'
 */
#include <stdio.h>
#include <string.h>

const char SYMBOLS[] = "0123456789ABCDEF";
const char *NIBBLE[16] = {
    "0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111",
    "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"
};

void to_binary(int n, char bits[])
{
    int power = 1, len = 0;
    while (power * 2 <= n)
        power = power * 2;
    do {
        if (n >= power) {
            bits[len] = '1';
            n = n - power;
        } else {
            bits[len] = '0';
        }
        len++;
        power = power / 2;
    } while (power > 0);
    bits[len] = '\0';
}

int from_binary(const char bits[])
{
    int n = strlen(bits), value = 0, i;
    for (i = 0; i < n; i++) {
        if (bits[i] == '1')
            value = value | (1 << (n - 1 - i));
    }
    return value;
}

void group_bits(const char bits[], int size, char out[])
{
    char padded[64];
    int n = strlen(bits);
    int pad = (size - n % size) % size;
    int i, j, k = 0;

    memset(padded, '0', pad);
    strcpy(padded + pad, bits);
    n += pad;
    for (i = 0; i < n; i += size) {
        int v = 0;
        for (j = 0; j < size; j++)
            v = 2 * v + (padded[i + j] == '1');
        out[k++] = SYMBOLS[v];
    }
    out[k] = '\0';
}

/* size is 3 for an octal digit and 4 for a hex digit: the last `size`
   characters of the 4-bit pattern are exactly the bits of that digit */
void expand_digits(const char text[], int size, char bits[])
{
    int i, start = 0;
    bits[0] = '\0';
    for (i = 0; text[i] != '\0'; i++)
        strcat(bits, NIBBLE[strchr(SYMBOLS, text[i]) - SYMBOLS] + (4 - size));
    while (bits[start] == '0' && bits[start + 1] != '\0')
        start++;
    memmove(bits, bits + start, strlen(bits + start) + 1);
}

int main(void)
{
    int values[5] = {9, 31, 128, 777, 3000};
    const char *inputs[4] = {"3FA", "BEEF", "755", "17"};
    int sizes[4] = {4, 4, 3, 3};
    char bits[80], octal[32], hex[32];
    int i;

    printf("decimal,binary,octal,hex,back_to_decimal\n");
    for (i = 0; i < 5; i++) {
        to_binary(values[i], bits);
        group_bits(bits, 3, octal);
        group_bits(bits, 4, hex);
        printf("%d,%s,%s,%s,%d\n", values[i], bits, octal, hex, from_binary(bits));
    }

    printf("\ninput,base,binary,decimal\n");
    for (i = 0; i < 4; i++) {
        expand_digits(inputs[i], sizes[i], bits);
        printf("%s,%d,%s,%d\n", inputs[i], sizes[i] == 4 ? 16 : 8, bits, from_binary(bits));
    }
    return 0;
}
