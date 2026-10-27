// Lab 8 - number systems (decimal, binary, octal, hexadecimal)
// Binary is printed straight from the bits using shifts and a mask.
// Octal and hex are printed by a recursive function: it prints the
// higher digits first and its own digit last, so no buffer and no
// reversing is needed. Text is turned back into a number by adding
// place values, starting from the rightmost digit.
#include <stdio.h>
#include <string.h>
#include <ctype.h>

// print the lowest `width` bits, with a space after every 4 bits
void show_binary(unsigned int value, int width)
{
    int bit;
    for (bit = width - 1; bit >= 0; bit--) {
        putchar(((value >> bit) & 1u) ? '1' : '0');
        if (bit % 4 == 0 && bit != 0)
            putchar(' ');
    }
}

// recursion unwinds from the most significant digit to the least
void show_in_base(unsigned int value, unsigned int base)
{
    unsigned int last = value % base;
    if (value >= base)
        show_in_base(value / base, base);
    if (last < 10)
        putchar('0' + last);
    else
        putchar('a' + last - 10);
}

// rightmost digit has weight 1, the next one base, then base*base ...
long parse_number(const char *str, int base)
{
    long total = 0, weight = 1;
    int i, digit;
    for (i = (int)strlen(str) - 1; i >= 0; i--) {
        char ch = (char)tolower((unsigned char)str[i]);
        digit = isdigit((unsigned char)ch) ? ch - '0' : ch - 'a' + 10;
        total += digit * weight;
        weight *= base;
    }
    return total;
}

// one output line per number, in all four systems
void report(unsigned int n)
{
    printf("n = %-6u bin ", n);
    show_binary(n, 16);
    printf("  oct ");
    show_in_base(n, 8);
    printf("  hex 0x");
    show_in_base(n, 16);
    putchar('\n');
}

int main(void)
{
    unsigned int samples[6] = {5, 42, 100, 511, 2024, 48879};
    const char *words[4] = {"101101", "644", "7E3", "cafe"};
    int bases[4] = {2, 8, 16, 16};
    int k;

    for (k = 0; k < 6; k++) {
        report(samples[k]);
    }
    printf("\n");
    // back to decimal, then show the same value in binary again as a check
    for (k = 0; k < 4; k++) {
        long value = parse_number(words[k], bases[k]);
        printf("\"%s\" base %-2d -> %5ld -> ", words[k], bases[k], value);
        show_binary((unsigned int)value, 16);
        putchar('\n');
    }
    return 0;
}
