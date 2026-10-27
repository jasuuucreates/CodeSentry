/* Assignment 4 - String Analysis
 * For each sample sentence: palindrome check, vowel and consonant count,
 * word frequency table and the sentence with its words in reverse order. */
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#define MAX_WORDS 50
#define WORD_LEN 32
#define BUF_LEN 256

/* Returns 1 if the letters and digits of text read the same both ways. */
int is_palindrome(const char *text) {
    char clean[BUF_LEN];
    int n = 0, i;
    i = 0;
    while (text[i] != '\0' && n < BUF_LEN - 1) {
        if (isalnum((unsigned char)text[i]))
            clean[n++] = (char)tolower((unsigned char)text[i]);
        i++;
    }
    i = 0;
    while (i < n / 2) {
        if (clean[i] != clean[n - 1 - i])
            return 0;
        i++;
    }
    return n > 0;
}

/* Counts vowels and consonants; the results go back through the pointers. */
void count_letters(const char *text, int *vowels, int *consonants) {
    int i;
    *vowels = *consonants = 0;
    i = 0;
    while (text[i] != '\0') {
        char c = (char)tolower((unsigned char)text[i]);
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u')
            (*vowels)++;
        else if (isalpha((unsigned char)c))
            (*consonants)++;
        i++;
    }
}

/* Counts every distinct word; strtok edits its input, so it scans a lower-case copy. */
int word_frequency(const char *text, char words[][WORD_LEN], int counts[]) {
    char buffer[BUF_LEN], *token;
    int total = 0, i;
    i = 0;
    while (text[i] != '\0' && i < BUF_LEN - 1) {
        buffer[i] = (char)tolower((unsigned char)text[i]);
        i++;
    }
    buffer[i] = '\0';
    token = strtok(buffer, " ,.!?");
    while (token != NULL) {
        int found = -1;
        i = 0;
        while (i < total) {
            if (strcmp(words[i], token) == 0)
                found = i;
            i++;
        }
        if (found >= 0) {
            counts[found]++;
        } else if (total < MAX_WORDS) {
            strncpy(words[total], token, WORD_LEN - 1);
            words[total][WORD_LEN - 1] = '\0';
            counts[total++] = 1;
        }
        token = strtok(NULL, " ,.!?");
    }
    return total;
}

/* Stores a pointer to every word, then prints them from the last to the first. */
void print_reversed(const char *text) {
    char buffer[BUF_LEN], *parts[MAX_WORDS], *token;
    int n = 0, i;
    strncpy(buffer, text, BUF_LEN - 1);
    buffer[BUF_LEN - 1] = '\0';
    token = strtok(buffer, " ");
    while (token != NULL && n < MAX_WORDS) {
        parts[n++] = token;
        token = strtok(NULL, " ");
    }
    i = n - 1;
    while (i >= 0) {
        printf("%s%s", parts[i], i > 0 ? " " : "");
        i--;
    }
    printf("\n");
}

int main(void) {
    const char *samples[] = {
        "Madam in Eden, I'm Adam",
        "the quick brown fox jumps over the lazy dog",
        "Never odd or even",
        "to be or not to be, that is the question"
    };
    int sample_count = (int)(sizeof(samples) / sizeof(samples[0]));
    char words[MAX_WORDS][WORD_LEN];
    int counts[MAX_WORDS], s, w, vowels, consonants, distinct;

    s = 0;
    while (s < sample_count) {
        printf("Sentence %d: %s\n", s + 1, samples[s]);
        printf("  Palindrome : %s\n", is_palindrome(samples[s]) ? "Yes" : "No");
        count_letters(samples[s], &vowels, &consonants);
        printf("  Vowels     : %d\n  Consonants : %d\n", vowels, consonants);
        printf("  Reversed   : ");
        print_reversed(samples[s]);
        distinct = word_frequency(samples[s], words, counts);
        printf("  Word frequency:\n");
        w = 0;
        while (w < distinct) {
            printf("    %-10s %d\n", words[w], counts[w]);
            w++;
        }
        printf("\n");
        s++;
    }
    return 0;
}
