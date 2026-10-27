"""Lab 7 - checking brackets in lines of code.

Instead of pushing the bracket characters, this version pushes their
POSITIONS. Remembering where every unmatched opener is lets the program
point at the exact character that is wrong with a ^ marker underneath.
"""

OPEN_SET = "([{"
CLOSE_SET = ")]}"


def kind_of(symbol):
    """Return (type number, is_opening) for a bracket, or None for anything else.

    The type number is the index in OPEN_SET / CLOSE_SET, so '(' and ')'
    both get type 0 and can be compared as plain integers.
    """
    if symbol in OPEN_SET:
        return OPEN_SET.index(symbol), True
    if symbol in CLOSE_SET:
        return CLOSE_SET.index(symbol), False
    return None


def first_error(line):
    """Index of the first wrong bracket in line, or -1 if everything matches."""
    positions = []
    for pos in range(len(line)):
        found = kind_of(line[pos])
        if found and found[1]:
            positions.append(pos)
        elif found:
            if not positions:
                return pos  # a closer with nothing open
            opener_type = kind_of(line[positions.pop()])[0]
            if opener_type != found[0]:
                return pos  # wrong kind of closer
    # an opener that was never closed: blame the innermost one
    return positions[-1] if positions else -1


def count_brackets(line):
    """How many bracket characters the line has (printed in the report)."""
    return sum(1 for c in line if kind_of(c) is not None)


def show(number, line, where):
    """Print one report line, plus a caret under the error when there is one."""
    tag = "OK" if where == -1 else "FAIL"
    prefix = "%2d) %-4s | " % (number, tag)
    print(prefix + line + "   [" + str(count_brackets(line)) + " brackets]")
    if where != -1:
        print(" " * (len(prefix) + where) + "^")


def main():
    tests = [
        "int f() { return a[(i + 1)]; }",
        "while (x < 10) { x = x * (2 + y]; }",
        "print((3 + 4) * 5)",
        "{[}]",
        "total = (a[0] + a[1]",
        "((())))",
    ]
    good = 0
    for t in range(len(tests)):
        where = first_error(tests[t])
        show(t + 1, tests[t], where)
        if where == -1:
            good += 1
    print()
    print("passed:", good, "/", len(tests))


if __name__ == "__main__":
    main()
