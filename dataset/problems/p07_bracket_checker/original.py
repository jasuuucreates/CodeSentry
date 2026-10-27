"""Assignment 7: Balanced Bracket Checker.

Checks a list of expressions and reports whether the brackets (), [] and {}
in each one are balanced. A Python list is used as a stack: every opening
bracket is pushed, and every closing bracket must match the bracket that is
popped from the top. The last bracket opened must be the first one closed,
which is exactly the last-in-first-out order a stack gives us.
"""

# Maps each closing bracket to the opening bracket it must match.
PAIRS = {")": "(", "]": "[", "}": "{"}


def is_opening(ch):
    """Return True if ch is one of the opening brackets."""
    return ch in PAIRS.values()


def is_closing(ch):
    """Return True if ch is one of the closing brackets."""
    return ch in PAIRS


def check_expression(expr):
    """Check one expression.

    Returns a tuple (balanced, message). The message explains the first
    problem found, so the user knows where to look.
    """
    stack = []
    for i in range(len(expr)):
        ch = expr[i]
        if is_opening(ch):
            stack.append(ch)
        elif is_closing(ch):
            if not stack:
                return False, "extra '" + ch + "' at index " + str(i)
            top = stack.pop()
            if top != PAIRS[ch]:
                return False, "'" + top + "' closed by '" + ch + "' at index " + str(i)
    # Anything still on the stack was opened but never closed.
    if stack:
        return False, str(len(stack)) + " bracket(s) left open"
    return True, "all brackets matched"


def print_report(expressions):
    """Print the result for every expression and return how many were balanced."""
    balanced_count = 0
    for i in range(len(expressions)):
        ok, message = check_expression(expressions[i])
        status = "Balanced" if ok else "Not balanced"
        print("Expression", i + 1, ":", expressions[i])
        print("    Result :", status, "(" + message + ")")
        if ok:
            balanced_count += 1
    return balanced_count


def main():
    expressions = [
        "(a + b) * [c - d]",
        "{[x * (y + z)] / 2}",
        "((1 + 2) * 3",
        "[a + b)",
        "a + b}",
        "{[()()]}",
        "}{",
        "if (arr[i] > max) { max = arr[i]; }",
    ]
    print("Balanced Bracket Checker")
    print("------------------------")
    total = print_report(expressions)
    print("------------------------")
    print("Balanced expressions:", total, "out of", len(expressions))


if __name__ == "__main__":
    main()
