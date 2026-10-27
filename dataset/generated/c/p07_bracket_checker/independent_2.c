/* Bracket checker (Lab 7)
 * The stack is a linked list built with malloc, so it has no fixed size. Each node
 * also stores the index of its bracket, so a ^ can be printed under the wrong one. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Node {
    char symbol;
    int index;
    struct Node *next;
};

static struct Node *head = NULL; /* top of the stack */

/* push a bracket together with its index; returns 0 if malloc fails */
int add_node(char symbol, int index)
{
    struct Node *fresh = malloc(sizeof(struct Node));
    if (fresh == NULL)
        return 0;
    fresh->symbol = symbol;
    fresh->index = index;
    fresh->next = head;
    head = fresh;
    return 1;
}

/* pop the top node into *symbol and *index; returns 0 when the stack is empty */
int remove_node(char *symbol, int *index)
{
    struct Node *old = head;
    if (old == NULL)
        return 0;
    *symbol = old->symbol;
    *index = old->index;
    head = old->next;
    free(old);
    return 1;
}

/* free every node still on the stack so the next line starts empty */
void free_list(void)
{
    char s;
    int i;
    while (head != NULL)
        remove_node(&s, &i);
}

/* index of the first bad bracket, or -1 if balanced. The loop stops once bad_at
 * is set, so there is one exit and the list is always freed before returning. */
int validate(const char *text)
{
    const char *opens = "([{", *closes = ")]}";
    int length = (int) strlen(text);
    int bad_at = -1, i, where;
    char last;

    for (i = 0; i < length && bad_at < 0; i++) {
        char *hit = strchr(closes, text[i]);
        if (strchr(opens, text[i]) != NULL) {
            if (!add_node(text[i], i))
                bad_at = i; /* out of memory: report where we had to stop */
        } else if (hit != NULL) {
            /* the popped opener must sit at the same position in "([{" */
            if (!remove_node(&last, &where) || last != opens[hit - closes])
                bad_at = i;
        }
    }
    if (bad_at < 0 && head != NULL)
        bad_at = head->index; /* innermost bracket that was never closed */
    free_list();
    return bad_at;
}

/* prints the text and, when pos is valid, a caret under that column */
void report(int number, const char *text, int pos)
{
    int k;
    printf("%d) %s\n   ", number, text);
    if (pos < 0) {
        printf("OK - brackets are balanced\n");
        return;
    }
    for (k = 0; k < pos; k++)
        putchar(' ');
    printf("^ problem at column %d\n", pos + 1);
}

int main(void)
{
    const char *lines[] = {"int f() { return a[(i + 1)]; }",
                           "while (x < 10) { x = x * (2 + y]; }",
                           "printf(\"%d\", (3 + 4) * 5);", "{[}]",
                           "sum = (a[0] + a[1]", "((())))"};
    int total = sizeof(lines) / sizeof(lines[0]), bad = 0, n;

    printf("=== Bracket validation ===\n\n");
    for (n = 0; n < total; n++) {
        int pos = validate(lines[n]);
        report(n + 1, lines[n], pos);
        if (pos >= 0)
            bad++;
    }
    printf("\n%d line(s) with errors, %d clean\n", bad, total - bad);
    return 0;
}
