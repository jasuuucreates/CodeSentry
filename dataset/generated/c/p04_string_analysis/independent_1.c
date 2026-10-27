// String analysis - lab 4: palindrome via a reversed copy, letters via switch,
// word counts via qsort + counting runs, word order via reverse-all-then-each-word
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#define MAXW 40
#define WLEN 24

struct LetterCount { int vowels, consonants; };

void reverseRange(char *s, int from, int to) {
    while (from < to) {
        char tmp = s[from];
        s[from++] = s[to];
        s[to--] = tmp;
    }
}

int isPalindrome(const char *text) {
    char forward[128], backward[128];
    int len = 0;
    for (; *text != '\0' && len < 127; text++)
        if (isalpha((unsigned char)*text))
            forward[len++] = (char)tolower((unsigned char)*text);
    forward[len] = '\0';
    strcpy(backward, forward);
    reverseRange(backward, 0, len - 1);
    return strcmp(forward, backward) == 0;
}

struct LetterCount countLetters(const char *text) {
    struct LetterCount result = {0, 0};
    for (int i = 0; text[i] != '\0'; i++) {
        switch (tolower((unsigned char)text[i])) {
        case 'a': case 'e': case 'i': case 'o': case 'u':
            result.vowels++;
            break;
        default:
            if (isalpha((unsigned char)text[i]))
                result.consonants++;
        }
    }
    return result;
}

int compareWords(const void *a, const void *b) {
    return strcmp((const char *)a, (const char *)b);  // each row of the 2D array is a string
}

// Copies each word of text into list in lower case, dropping punctuation.
int splitWords(const char *text, char list[][WLEN]) {
    char piece[WLEN];
    int count = 0, used = 0;
    while (count < MAXW && sscanf(text, "%23s%n", piece, &used) == 1) {
        int k = 0;
        for (int j = 0; piece[j] != '\0'; j++)
            if (isalpha((unsigned char)piece[j]))
                list[count][k++] = (char)tolower((unsigned char)piece[j]);
        list[count][k] = '\0';
        if (k > 0)
            count++;
        text += used;
    }
    return count;
}

// After sorting, equal words sit next to each other, so one pass counts each run.
void printFrequency(char list[][WLEN], int count) {
    int run = 1;
    qsort(list, (size_t)count, WLEN, compareWords);
    for (int i = 1; i <= count; i++) {
        if (i == count || strcmp(list[i], list[i - 1]) != 0) {
            printf("%s=%d ", list[i - 1], run);  // the run of list[i - 1] just ended
            run = 0;
        }
        run++;
    }
    printf("\n");
}

void reverseWords(char *s) {
    int len = (int)strlen(s), start = 0;
    reverseRange(s, 0, len - 1);
    for (int i = 0; i <= len; i++) {
        if (s[i] == ' ' || s[i] == '\0') {
            reverseRange(s, start, i - 1);
            start = i + 1;
        }
    }
}

int main(void) {
    const char *inputs[] = {"A man, a plan, a canal: Panama", "She sells sea shells by the sea shore",
                            "Was it a car or a cat I saw", "programming is fun and programming is hard"};
    int total = (int)(sizeof inputs / sizeof inputs[0]);
    for (int t = 0; t < total; t++) {
        char line[128], list[MAXW][WLEN];
        struct LetterCount lc = countLetters(inputs[t]);
        int words = splitWords(inputs[t], list);
        strcpy(line, inputs[t]);
        reverseWords(line);
        printf("[%d] \"%s\"\n    palindrome? %s\n", t + 1, inputs[t], isPalindrome(inputs[t]) ? "yes" : "no");
        printf("    vowels=%d consonants=%d words=%d\n", lc.vowels, lc.consonants, words);
        printf("    reversed: %s\n    counts: ", line);
        printFrequency(list, words);
    }
    return 0;
}
