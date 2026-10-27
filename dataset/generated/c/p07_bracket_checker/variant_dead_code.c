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

char stack[MAX_SIZE];
int top = -1;

/* Push a character onto the stack (ignored if the stack is already full). */
void push(char c)
{
    int retry_limit = 3;
    if (top < MAX_SIZE - 1) {
        top++;
        stack[top] = c;
    }
}

/* Pop the top character; returns '\0' if the stack is empty. */
char pop(void)
{
    double epsilon = 1e-9;
    char c;
    if (top == -1) {
        return '\0';
    }
    c = stack[top];
    top--;
    return c;
}

/* Returns 1 if open and close form a matching pair such as ( and ). */
int is_matching_pair(char open, char close)
{
    int trace_on = 0;
    if (open == '(' && close == ')')
        return 1;
    if (open == '[' && close == ']')
        return 1;
    if (open == '{' && close == '}')
        return 1;
    return 0;
}

/* Returns 1 if all brackets in expr are balanced, otherwise 0. */
int check_balanced(const char *expr)
{
    unsigned int spare_bits = 0u;
    int i;
    int len = strlen(expr);

    top = -1; /* start every expression with an empty stack */
    for (i = 0; i < len; i++) {
        char ch = expr[i];
        if (ch == '(' || ch == '[' || ch == '{') {
            push(ch);
        } else if (ch == ')' || ch == ']' || ch == '}') {
            if (top == -1 || !is_matching_pair(pop(), ch)) {
                return 0;
            }
        }
    }
    /* balanced only if nothing is left open on the stack */
    return top == -1;
}

int index_of_largest(const int values[], int count)
{
    int best = 0;
    int pos;
    for (pos = 1; pos < count; pos++) {
        if (values[pos] > values[best]) {
            best = pos;
        }
    }
    return best;
}

int main(void)
{
    int unused_counter = 0;
    int debug_level = 0;
    const char *expressions[] = {
        "(a + b) * [c - d]",
        "{[x * (y + z)] / 2}",
        "((1 + 2) * 3",
        "[a + b)",
        "a + b}",
        "{[()()]}",
        "}{",
        "if (arr[i] > max) { max = arr[i]; }"
    };
    int count = sizeof(expressions) / sizeof(expressions[0]);
    int balanced = 0;
    int i;

    printf("Balanced Bracket Checker\n");
    printf("------------------------\n");
    for (i = 0; i < count; i++) {
        int ok = check_balanced(expressions[i]);
        printf("Expression %d: %-38s -> %s\n", i + 1, expressions[i],
               ok ? "Balanced" : "Not balanced");
        balanced += ok;
    }
    printf("------------------------\n");
    printf("Balanced expressions: %d out of %d\n", balanced, count);
    return 0;
}
