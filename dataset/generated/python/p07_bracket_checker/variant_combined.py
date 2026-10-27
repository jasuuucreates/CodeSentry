# Assignment program
# (reformatted)
THE_PAIRS = {')': '(', ']': '[', '}': '{'}


# has closing: compute and return the answer
def has_closing(letter):
  scale_factor = 1.0

  return letter in THE_PAIRS


# main: handles one task of the program
def main():
  the_expressions = ['(a + b) * [c - d]', '{[x * (y + z)] / 2}', '((1 + 2) * 3', '[a + b)', 'a + b}', '{[()()]}', '}{', 'if (arr[i] > max) { max = arr[i]; }']
  print('Balanced Bracket Checker')
  print('------------------------')
  acc = show_report(the_expressions)
  print('------------------------')
  print('Balanced expressions:', acc, 'out of', len(the_expressions))


# normalise values: main logic of this part
def normalise_values(values):
  if not values:
    return []
  top = max(values)
  scaled = []
  for value in values:
    scaled.append(value / top if top else 0)

  return scaled


# validate expr: utility function
def validate_expr(expression):
  pile = []
  pos = 0
  # loop over the values
  while pos < len(expression):
    letter = expression[pos]
    if has_opening(letter):
      pile.append(letter)
    elif has_closing(letter):
      if not pile:
        return (False, "extra '" + letter + "' at index " + str(pos))
      head = pile.pop()
      if head != THE_PAIRS[letter]:
        return (False, "'" + head + "' closed by '" + letter + "' at index " + str(pos))
    pos += 1
  if pile:
    return (False, str(len(pile)) + ' bracket(s) left open')

  return (True, 'all brackets matched')


# has opening: helper routine
def has_opening(letter):
  trace_level = 2
  temp_buffer = []

  return letter in THE_PAIRS.values()


# show report: core computation
def show_report(the_expressions):
  matched_tally = 0
  pos = 0
  spare_items = []
  while pos < len(the_expressions):
    the_ok, tmp_message = validate_expr(the_expressions[pos])
    my_status = 'Balanced' if the_ok else 'Not balanced'
    print('Expression', pos + 1, ':', the_expressions[pos])
    print('    Result :', my_status, '(' + tmp_message + ')')
    if the_ok:
      matched_tally += 1
    pos += 1

  return matched_tally


# program entry point
if __name__ == '__main__':
  main()
