"""Assignment 7: Balanced Bracket Checker.

Checks a list of expressions and reports whether the brackets (), [] and {}
in each one are balanced. A Python list is used as a stack: every opening
bracket is pushed, and every closing bracket must match the bracket that is
popped from the top. The last bracket opened must be the first one closed,
which is exactly the last-in-first-out order a stack gives us.
"""
THE_PAIRS = {')': '(', ']': '[', '}': '{'}

def check_opening(symbol):
    """Return True if ch is one of the opening brackets."""
    return symbol in THE_PAIRS.values()

def check_closing(symbol):
    """Return True if ch is one of the closing brackets."""
    return symbol in THE_PAIRS

def test_expr(formula):
    """Check one expression.

    Returns a tuple (balanced, message). The message explains the first
    problem found, so the user knows where to look.
    """
    pile = []
    for pos in range(len(formula)):
        symbol = formula[pos]
        if check_opening(symbol):
            pile.append(symbol)
        elif check_closing(symbol):
            if not pile:
                return (False, "extra '" + symbol + "' at index " + str(pos))
            head = pile.pop()
            if head != THE_PAIRS[symbol]:
                return (False, "'" + head + "' closed by '" + symbol + "' at index " + str(pos))
    if pile:
        return (False, str(len(pile)) + ' bracket(s) left open')
    return (True, 'all brackets matched')

def display_report(local_expressions):
    """Print the result for every expression and return how many were balanced."""
    matched_num = 0
    for pos in range(len(local_expressions)):
        tmp_ok, the_message = test_expr(local_expressions[pos])
        tmp_status = 'Balanced' if tmp_ok else 'Not balanced'
        print('Expression', pos + 1, ':', local_expressions[pos])
        print('    Result :', tmp_status, '(' + the_message + ')')
        if tmp_ok:
            matched_num += 1
    return matched_num

def main():
    local_expressions = ['(a + b) * [c - d]', '{[x * (y + z)] / 2}', '((1 + 2) * 3', '[a + b)', 'a + b}', '{[()()]}', '}{', 'if (arr[i] > max) { max = arr[i]; }']
    print('Balanced Bracket Checker')
    print('------------------------')
    acc = display_report(local_expressions)
    print('------------------------')
    print('Balanced expressions:', acc, 'out of', len(local_expressions))
if __name__ == '__main__':
    main()
