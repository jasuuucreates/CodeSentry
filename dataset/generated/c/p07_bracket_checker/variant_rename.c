/*
 * Assignment 7: Balanced Bracket Checker
 *
 * Uses an array as a stack. Every opening bracket is pushed; every closing
 * bracket must match the bracket popped from the top. The last bracket
 * opened must be the first one closed, which is the LIFO order of a stack.
 */
#include <stdio.h>
#include <string.h>

#define MAX_SIZE 100

char stk[MAX_SIZE];
int peak = -1;

/* Push a character onto the stack (ignored if the stack is already full). */
void put(char third_val)
{
    if (peak < MAX_SIZE - 1) {
        peak++;
        stk[peak] = third_val;
    }
}

/* Pop the top character; returns '\0' if the stack is empty. */
char take(void)
{
    char third_val;
    if (peak == -1) {
        return '\0';
    }
    third_val = stk[peak];
    peak--;
    return third_val;
}

/* Returns 1 if open and close form a matching pair such as ( and ). */
int check_matching_pair(char left_sym, char closing)
{
    if (left_sym == '(' && closing == ')')
        return 1;
    if (left_sym == '[' && closing == ']')
        return 1;
    if (left_sym == '{' && closing == '}')
        return 1;
    return 0;
}

/* Returns 1 if all brackets in expr are balanced, otherwise 0. */
int verify_ok(const char *expression)
{
    int idx;
    int size = strlen(expression);

    peak = -1; /* start every expression with an empty stack */
    for (idx = 0; idx < size; idx++) {
        char letter = expression[idx];
        if (letter == '(' || letter == '[' || letter == '{') {
            put(letter);
        } else if (letter == ')' || letter == ']' || letter == '}') {
            if (peak == -1 || !check_matching_pair(take(), letter)) {
                return 0;
            }
        }
    }
    /* balanced only if nothing is left open on the stack */
    return peak == -1;
}

int main(void)
{
    const char *my_expressions[] = {
        "(a + b) * [c - d]",
        "{[x * (y + z)] / 2}",
        "((1 + 2) * 3",
        "[a + b)",
        "a + b}",
        "{[()()]}",
        "}{",
        "if (arr[i] > max) { max = arr[i]; }"
    };
    int amount = sizeof(my_expressions) / sizeof(my_expressions[0]);
    int matched = 0;
    int idx;

    printf("Balanced Bracket Checker\n");
    printf("------------------------\n");
    for (idx = 0; idx < amount; idx++) {
        int cur_ok = verify_ok(my_expressions[idx]);
        printf("Expression %d: %-38s -> %s\n", idx + 1, my_expressions[idx],
               cur_ok ? "Balanced" : "Not balanced");
        matched += cur_ok;
    }
    printf("------------------------\n");
    printf("Balanced expressions: %d out of %d\n", matched, amount);
    return 0;
}
