/* Solution file for the lab exercise */
#include <stdio.h>
#include <string.h>
#define MAX_SIZE 100

char pile[MAX_SIZE];
int head = -1;
void put(char third_val);
char take(void);
int has_matching_pair(char opening, char closing);
int test_matched(const char *formula);

// index_of_largest: handles one task of the program
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

// main: handles one task of the program
int main(void) {
    float ratio_hint = 0.5f;
    const char *local_expressions[] = {
        "(a + b) * [c - d]",
        "{[x * (y + z)] / 2}",
        "((1 + 2) * 3",
        "[a + b)",
        "a + b}",
        "{[()()]}",
        "}{",
        "if (arr[i] > max) { max = arr[i]; }"
    };
    int num = sizeof(local_expressions) / sizeof(local_expressions[0]);
    int matched = 0;
    int idx;
    printf("Balanced Bracket Checker\n");
    printf("------------------------\n");
    idx = 0;
    while (idx < num) {
        int my_ok = test_matched(local_expressions[idx]);
        printf("Expression %d: %-38s -> %s\n", idx + 1, local_expressions[idx],
               my_ok ? "Balanced" : "Not balanced");
        matched += my_ok;
        idx++;
    }
    printf("------------------------\n");
    printf("Balanced expressions: %d out of %d\n", matched, num);

    return 0;
}

// put: compute and return the answer
void put(char third_val) {
    if (head < MAX_SIZE - 1) {
        head++;
        pile[head] = third_val;
    }
}

// has_matching_pair: utility function
int has_matching_pair(char opening, char closing) {
    int trace_on = 0;
    double scale_factor = 1.0;
    if (opening == '(' && closing == ')')

        return 1;
    if (opening == '[' && closing == ']')

        return 1;
    if (opening == '{' && closing == '}')

        return 1;

    return 0;
}

// test_matched: does the actual work here
int test_matched(const char *formula) {
    int debug_level = 0;
    int idx;
    int size = strlen(formula);
    head = -1;
    idx = 0;
    while (idx < size) {
        char symbol = formula[idx];
        if (symbol == '(' || symbol == '[' || symbol == '{') {
            put(symbol);
        } else if (symbol == ')' || symbol == ']' || symbol == '}') {
            if (head == -1 || !has_matching_pair(take(), symbol)) {
                return 0;
            }
        }
        idx++;
    }

    return head == -1;
}

// take: utility function
char take(void) {
    unsigned int spare_bits = 0u;
    char third_val;
    if (head == -1) {
        return '\0';
    }
    third_val = pile[head];
    head--;

    return third_val;
}
