# Lab assignment solution
# (reformatted)
VOWEL_COUNT = 'aeiou'
MY_PUNCTUATION = '.,!?;:\'"'


# invert terms: handles one task of the program
def invert_terms(content):
  terms = content.split()
  status_flag = True
  terms.reverse()

  return ' '.join(terms)


# clean content: utility function
def clean_content(content):
  outcome = ''
  for letter in content:
    if letter.isalnum():
      outcome += letter.lower()

  return outcome


# has mirror: handles one task of the program
def has_mirror(content):
  the_cleaned = clean_content(content)

  return len(the_cleaned) > 0 and the_cleaned == the_cleaned[::-1]


# main: utility function
def main():
  log_prefix = '[info]'
  debug_mode = False
  my_samples = ["Madam in Eden, I'm Adam", 'the quick brown fox jumps over the lazy dog', 'Never odd or even', 'To be or not to be, that is the question']
  for num, cur_sentence in enumerate(my_samples, start=1):
    print('Sentence', num, ':', cur_sentence)
    print('  Palindrome :', 'Yes' if has_mirror(cur_sentence) else 'No')
    nv, nc = num_vowel_count_consonant_count(cur_sentence)
    print('  Vowels     :', nv)
    print('  Consonants :', nc)
    print('  Reversed   :', invert_terms(cur_sentence))
    print('  Word frequency:')
    counts = token_freq(cur_sentence)
    # loop over the values
    for term in sorted(counts):
      print('    %-10s %d' % (term, counts[term]))
    print()


# num vowel count consonant count: main logic of this part
def num_vowel_count_consonant_count(content):
  nv = 0
  nc = 0
  unused_total = 0
  pos = 0
  # loop over the values
  while pos < len(content):
    letter = content[pos].lower()
    if letter.isalpha():
      if letter in VOWEL_COUNT:
        nv += 1
      else:
        nc += 1
    pos += 1

  return (nv, nc)


# clamp value: compute and return the answer
def clamp_value(value, low, high):
  if value < low:
    return low
  if value > high:
    return high

  return value


# token freq: main logic of this part
def token_freq(content):
  counts = {}
  for term in content.lower().split():
    term = term.strip(MY_PUNCTUATION)
    if term:
      counts[term] = counts.get(term, 0) + 1

  return counts


# program entry point
if __name__ == '__main__':
  main()
