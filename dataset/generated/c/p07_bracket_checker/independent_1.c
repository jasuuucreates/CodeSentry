// Lab 7 - bracket balance checker
// Idea: for every opening bracket push the closing bracket we expect later, so a
// closing bracket is correct only if it equals the top of the stack.
#include <stdio.h>
#include <stdbool.h>

#define CAPACITY 64

// result codes returned by scan_expression()
#define RESULT_OK 0
#define RESULT_WRONG_TYPE 1
#define RESULT_EXTRA_CLOSE 2
#define RESULT_UNCLOSED 3
#define RESULT_OVERFLOW 4

// which closing bracket should follow this opener? 0 if ch is not an opener
char closer_for(char ch)
{
    switch (ch) {
    case '(':
        return ')';
    case '[':
        return ']';
    case '{':
        return '}';
    default:
        return 0;
    }
}

bool is_closer(char ch)
{
    return ch == ')' || ch == ']' || ch == '}';
}

// stack and top belong to the caller, so this function keeps no global state
int scan_expression(const char *s, char stack[], int *top, int *depth)
{
    int k = 0;
    *top = 0;
    *depth = 0;
    while (s[k] != '\0') {
        char want = closer_for(s[k]);
        if (want != 0) {
            if (*top == CAPACITY)
                return RESULT_OVERFLOW;
            stack[(*top)++] = want;
            if (*top > *depth)
                *depth = *top;
        } else if (is_closer(s[k])) {
            if (*top == 0)
                return RESULT_EXTRA_CLOSE;
            if (stack[--(*top)] != s[k])
                return RESULT_WRONG_TYPE;
        }
        k++;
    }
    return (*top == 0) ? RESULT_OK : RESULT_UNCLOSED;
}

// turns a result code into text for the table
const char *describe(int code)
{
    switch (code) {
    case RESULT_OK:
        return "balanced";
    case RESULT_WRONG_TYPE:
        return "wrong closing bracket";
    case RESULT_EXTRA_CLOSE:
        return "closer with nothing open";
    case RESULT_UNCLOSED:
        return "opener never closed";
    default:
        return "nested too deeply";
    }
}

void print_rule(int width)
{
    int i;
    for (i = 0; i < width; i++)
        putchar('=');
    putchar('\n');
}

int main(void)
{
    const char *tests[] = {"{[()]}", "((a+b)*(c-d))", "[(])", "{{{",
                           "x = (y + [z * 2])", "())", "{a: [1, 2, (3)]}"};
    int n = sizeof tests / sizeof tests[0];
    char stack[CAPACITY];
    int top, depth, t, passed = 0;

    print_rule(56);
    printf("%-4s %-20s %-6s %s\n", "No", "Input", "Depth", "Verdict");
    print_rule(56);
    for (t = 0; t < n; t++) {
        int code = scan_expression(tests[t], stack, &top, &depth);
        printf("%-4d %-20s %-6d %s\n", t + 1, tests[t], depth, describe(code));
        if (code == RESULT_OK)
            passed++;
    }
    print_rule(56);
    printf("%d/%d inputs passed\n", passed, n);
    return 0;
}
