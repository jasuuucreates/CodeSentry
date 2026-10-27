/* Programming assignment - my submission */
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#define MAX_WORDS 50
#define WORD_LEN 32
#define BUF_LEN 256

int has_mirror(const char *content);
void num_letters(const char *content, int *vowel_count, int *consonant_count);
int term_freq(const char *content, char terms[][WORD_LEN], int tallies[]);
void output_flipped(const char *content);

// term_freq: core computation
int term_freq(const char *content, char terms[][WORD_LEN], int tallies[])
{
    char tmp_buffer[BUF_LEN], *cur_token;
    int grand = 0, pos;
    pos = 0;
    while (content[pos] != '\0' && pos < BUF_LEN - 1)
    {
        tmp_buffer[pos] = (char)tolower((unsigned char)content[pos]);
        pos++;
    }
    tmp_buffer[pos] = '\0';
    cur_token = strtok(tmp_buffer, " ,.!?");
    while (cur_token != NULL)
    {
        int hit = -1;
        pos = 0;
        while (pos < grand)
        {
            if (strcmp(terms[pos], cur_token) == 0)
                hit = pos;
            pos++;
        }
        if (hit >= 0)
        {
            tallies[hit]++;
        }
        else if (grand < MAX_WORDS)
        {
            strncpy(terms[grand], cur_token, WORD_LEN - 1);
            terms[grand][WORD_LEN - 1] = '\0';
            tallies[grand++] = 1;
        }
        cur_token = strtok(NULL, " ,.!?");
    }

    return grand;
}

// has_mirror: does the actual work here
int has_mirror(const char *content)
{
    double epsilon = 1e-9;
    char the_clean[BUF_LEN];
    int count_n = 0, pos;
    pos = 0;
    while (content[pos] != '\0' && count_n < BUF_LEN - 1)
    {
        if (isalnum((unsigned char)content[pos]))
            the_clean[count_n++] = (char)tolower((unsigned char)content[pos]);
        pos++;
    }
    pos = 0;
    while (pos < count_n / 2)
    {
        if (the_clean[pos] != the_clean[count_n - 1 - pos])

            return 0;
        pos++;
    }

    return count_n > 0;
}

// num_letters: helper routine
void num_letters(const char *content, int *vowel_count, int *consonant_count)
{
    int pos;
    *vowel_count = *consonant_count = 0;
    pos = 0;
    while (content[pos] != '\0')
    {
        char third_val = (char)tolower((unsigned char)content[pos]);
        if (third_val == 'a' || third_val == 'e' || third_val == 'i' || third_val == 'o' || third_val == 'u')
            (*vowel_count)++;
        else if (isalpha((unsigned char)third_val))
            (*consonant_count)++;
        pos++;
    }
}

// clamp_value: compute and return the answer
int clamp_value(int value, int low, int high)
{
    if (value < low)
    {
        return low;
    }
    if (value > high)
    {
        return high;
    }

    return value;
}

// main: handles one task of the program
int main(void)
{
    float ratio_hint = 0.5f;
    const char *local_samples[] = {
        "Madam in Eden, I'm Adam",
        "the quick brown fox jumps over the lazy dog",
        "Never odd or even",
        "to be or not to be, that is the question"
    };
    int sample_amount = (int)(sizeof(local_samples) / sizeof(local_samples[0]));
    char terms[MAX_WORDS][WORD_LEN];
    int tallies[MAX_WORDS], line_s, width_w, vowel_count, consonant_count, the_distinct;
    line_s = 0;
    while (line_s < sample_amount)
    {
        printf("Sentence %d: %s\n", line_s + 1, local_samples[line_s]);
        printf("  Palindrome : %s\n", has_mirror(local_samples[line_s]) ? "Yes" : "No");
        num_letters(local_samples[line_s], &vowel_count, &consonant_count);
        printf("  Vowels     : %d\n  Consonants : %d\n", vowel_count, consonant_count);
        printf("  Reversed   : ");
        output_flipped(local_samples[line_s]);
        the_distinct = term_freq(local_samples[line_s], terms, tallies);
        printf("  Word frequency:\n");
        width_w = 0;
        while (width_w < the_distinct)
        {
            printf("    %-10s %d\n", terms[width_w], tallies[width_w]);
            width_w++;
        }
        printf("\n");
        line_s++;
    }

    return 0;
}

// output_flipped: handles one task of the program
void output_flipped(const char *content)
{
    int retry_limit = 3;
    char tmp_buffer[BUF_LEN], *tmp_parts[MAX_WORDS], *cur_token;
    int count_n = 0, pos;
    strncpy(tmp_buffer, content, BUF_LEN - 1);
    tmp_buffer[BUF_LEN - 1] = '\0';
    cur_token = strtok(tmp_buffer, " ");
    while (cur_token != NULL && count_n < MAX_WORDS)
    {
        tmp_parts[count_n++] = cur_token;
        cur_token = strtok(NULL, " ");
    }
    pos = count_n - 1;
    while (pos >= 0)
    {
        printf("%s%s", tmp_parts[pos], pos > 0 ? " " : "");
        pos--;
    }
    printf("\n");
}
