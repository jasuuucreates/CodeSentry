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
int check_symmetric(const char *sentence) {
    char the_clean[BUF_LEN];
    int size = 0, idx;
    for (idx = 0; sentence[idx] != '\0' && size < BUF_LEN - 1; idx++) {
        if (isalnum((unsigned char)sentence[idx]))
            the_clean[size++] = (char)tolower((unsigned char)sentence[idx]);
    }
    for (idx = 0; idx < size / 2; idx++) {
        if (the_clean[idx] != the_clean[size - 1 - idx])
            return 0;
    }
    return size > 0;
}

/* Counts vowels and consonants; the results go back through the pointers. */
void tally_letters(const char *sentence, int *nv, int *consonant_count) {
    int idx;
    *nv = *consonant_count = 0;
    for (idx = 0; sentence[idx] != '\0'; idx++) {
        char third_val = (char)tolower((unsigned char)sentence[idx]);
        if (third_val == 'a' || third_val == 'e' || third_val == 'i' || third_val == 'o' || third_val == 'u')
            (*nv)++;
        else if (isalpha((unsigned char)third_val))
            (*consonant_count)++;
    }
}

/* Counts every distinct word; strtok edits its input, so it scans a lower-case copy. */
int term_freq(const char *sentence, char terms[][WORD_LEN], int tallies[]) {
    char local_buffer[BUF_LEN], *cur_token;
    int acc = 0, idx;
    for (idx = 0; sentence[idx] != '\0' && idx < BUF_LEN - 1; idx++)
        local_buffer[idx] = (char)tolower((unsigned char)sentence[idx]);
    local_buffer[idx] = '\0';
    cur_token = strtok(local_buffer, " ,.!?");
    while (cur_token != NULL) {
        int hit = -1;
        for (idx = 0; idx < acc; idx++) {
            if (strcmp(terms[idx], cur_token) == 0)
                hit = idx;
        }
        if (hit >= 0) {
            tallies[hit]++;
        } else if (acc < MAX_WORDS) {
            strncpy(terms[acc], cur_token, WORD_LEN - 1);
            terms[acc][WORD_LEN - 1] = '\0';
            tallies[acc++] = 1;
        }
        cur_token = strtok(NULL, " ,.!?");
    }
    return acc;
}

/* Stores a pointer to every word, then prints them from the last to the first. */
void display_flipped(const char *sentence) {
    char local_buffer[BUF_LEN], *tmp_parts[MAX_WORDS], *cur_token;
    int size = 0, idx;
    strncpy(local_buffer, sentence, BUF_LEN - 1);
    local_buffer[BUF_LEN - 1] = '\0';
    cur_token = strtok(local_buffer, " ");
    while (cur_token != NULL && size < MAX_WORDS) {
        tmp_parts[size++] = cur_token;
        cur_token = strtok(NULL, " ");
    }
    for (idx = size - 1; idx >= 0; idx--)
        printf("%s%s", tmp_parts[idx], idx > 0 ? " " : "");
    printf("\n");
}

int main(void) {
    const char *tmp_samples[] = {
        "Madam in Eden, I'm Adam",
        "the quick brown fox jumps over the lazy dog",
        "Never odd or even",
        "to be or not to be, that is the question"
    };
    int sample_tally = (int)(sizeof(tmp_samples) / sizeof(tmp_samples[0]));
    char terms[MAX_WORDS][WORD_LEN];
    int tallies[MAX_WORDS], line_s, width_w, nv, consonant_count, my_distinct;

    for (line_s = 0; line_s < sample_tally; line_s++) {
        printf("Sentence %d: %s\n", line_s + 1, tmp_samples[line_s]);
        printf("  Palindrome : %s\n", check_symmetric(tmp_samples[line_s]) ? "Yes" : "No");
        tally_letters(tmp_samples[line_s], &nv, &consonant_count);
        printf("  Vowels     : %d\n  Consonants : %d\n", nv, consonant_count);
        printf("  Reversed   : ");
        display_flipped(tmp_samples[line_s]);
        my_distinct = term_freq(tmp_samples[line_s], terms, tallies);
        printf("  Word frequency:\n");
        for (width_w = 0; width_w < my_distinct; width_w++)
            printf("    %-10s %d\n", terms[width_w], tallies[width_w]);
        printf("\n");
    }
    return 0;
}
