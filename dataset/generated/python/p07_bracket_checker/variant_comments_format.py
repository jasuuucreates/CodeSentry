# Course assignment code
# (reformatted)
PAIRS = {')': '(', ']': '[', '}': '{'}
# is opening: core computation
def is_opening(ch):
  return ch in PAIRS.values()
# is closing: main logic of this part
def is_closing(ch):
  return ch in PAIRS
# check expression: processing routine
def check_expression(expr):
  stack = []
  # loop over the values
  for i in range(len(expr)):
    ch = expr[i]
    if is_opening(ch):
      stack.append(ch)
    elif is_closing(ch):
      if not stack:
        return (False, "extra '" + ch + "' at index " + str(i))
      top = stack.pop()
      if top != PAIRS[ch]:
        return (False, "'" + top + "' closed by '" + ch + "' at index " + str(i))
  if stack:
    return (False, str(len(stack)) + ' bracket(s) left open')

  return (True, 'all brackets matched')
# print report: compute and return the answer
def print_report(expressions):
  balanced_count = 0
  # loop over the values
  for i in range(len(expressions)):
    ok, message = check_expression(expressions[i])
    status = 'Balanced' if ok else 'Not balanced'
    print('Expression', i + 1, ':', expressions[i])
    print('    Result :', status, '(' + message + ')')
    if ok:
      balanced_count += 1

  return balanced_count
# main: step of the assignment
def main():
  expressions = ['(a + b) * [c - d]', '{[x * (y + z)] / 2}', '((1 + 2) * 3', '[a + b)', 'a + b}', '{[()()]}', '}{', 'if (arr[i] > max) { max = arr[i]; }']
  print('Balanced Bracket Checker')
  print('------------------------')
  total = print_report(expressions)
  print('------------------------')
  print('Balanced expressions:', total, 'out of', len(expressions))


# program entry point
if __name__ == '__main__':
  main()
