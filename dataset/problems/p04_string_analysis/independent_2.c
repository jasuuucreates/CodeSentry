/* ===== LAB 4 : string analysis =====
 * recursive palindrome test, vowels vs consonants, word table with a
 * star histogram, and the words of each sentence printed last to first */
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#define TABLE_SIZE 40

typedef struct {
    char word[20];
    int count;
} Entry;

/* skip non-letters at either end, compare the two outer letters, then recurse inward */
static bool pal_check(const char *s, int lo, int hi) {
    if (lo >= hi) return true;                  /* 0 or 1 character left */
    if (!isalpha((unsigned char)s[lo])) return pal_check(s, lo + 1, hi);
    if (!isalpha((unsigned char)s[hi])) return pal_check(s, lo, hi - 1);
    if (tolower((unsigned char)s[lo]) != tolower((unsigned char)s[hi])) return false;
    return pal_check(s, lo + 1, hi - 1);
}

static int count_vowels(const char *s, int *letters) {
    int vowels = 0;
    *letters = 0;
    while (*s) {
        if (isalpha((unsigned char)*s)) {
            (*letters)++;
            if (strchr("aeiouAEIOU", *s) != NULL) vowels++;
        }
        s++;
    }
    return vowels;
}

/* one more occurrence of word; when the table is full new words are ignored */
static void add_word(Entry table[], int *size, const char *word) {
    int i;
    for (i = 0; i < *size; i++) {
        if (strcmp(table[i].word, word) == 0) {
            table[i].count++;
            return;
        }
    }
    if (*size < TABLE_SIZE) {
        strcpy(table[*size].word, word);
        table[(*size)++].count = 1;
    }
}

/* reads character by character; the terminating '\0' also closes the last word */
static int build_table(const char *s, Entry table[]) {
    char current[20];
    int len = 0, size = 0;
    do {
        if (isalpha((unsigned char)*s)) {
            if (len < 19) current[len++] = (char)tolower((unsigned char)*s);
        } else if (len > 0) {
            current[len] = '\0';
            add_word(table, &size, current);
            len = 0;
        }
    } while (*s++ != '\0');
    return size;
}

/* walks from the end: skip spaces, find where the word starts, print it, repeat */
static void print_words_backwards(const char *s) {
    int end = (int)strlen(s), start;
    while (end > 0) {
        while (end > 0 && s[end - 1] == ' ') end--;
        start = end;
        while (start > 0 && s[start - 1] != ' ') start--;
        if (start < end) printf("%.*s%s", end - start, s + start, start > 0 ? " " : "");
        end = start;
    }
    putchar('\n');
}

int main(void) {
    const char *text[4] = {
        "Step on no pets",
        "the cat and the hat and the bat",
        "Rise to vote, sir",
        "C code is easy to read and easy to write"
    };
    Entry table[TABLE_SIZE];
    int n, i, k, letters, vowels, distinct;

    for (n = 0; n < 4; n++) {
        vowels = count_vowels(text[n], &letters);
        printf("---- text %d ----\n  input      : %s\n", n + 1, text[n]);
        printf("  palindrome : %s\n",
               pal_check(text[n], 0, (int)strlen(text[n]) - 1) ? "true" : "false");
        printf("  letters    : %d (%d vowels, %d consonants)\n", letters, vowels, letters - vowels);
        printf("  backwards  : ");
        print_words_backwards(text[n]);
        distinct = build_table(text[n], table);
        printf("  frequency  : %d distinct words\n", distinct);
        for (i = 0; i < distinct; i++) {
            printf("      %-8s ", table[i].word);
            for (k = 0; k < table[i].count; k++) putchar('*');
            printf(" %d\n", table[i].count);
        }
    }
    return 0;
}
