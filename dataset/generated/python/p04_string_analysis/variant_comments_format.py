# Lab assignment solution
# (reformatted)
VOWELS = 'aeiou'
PUNCTUATION = '.,!?;:\'"'


# clean text: small helper used below
def clean_text(text):
  result = ''
  for ch in text:
    if ch.isalnum():
      result += ch.lower()

  return result


# is palindrome: core computation
def is_palindrome(text):
  cleaned = clean_text(text)

  return len(cleaned) > 0 and cleaned == cleaned[::-1]


# count vowels consonants: small helper used below
def count_vowels_consonants(text):
  vowels = 0
  consonants = 0
  # loop over the values
  for i in range(len(text)):
    ch = text[i].lower()
    if ch.isalpha():
      if ch in VOWELS:
        vowels += 1
      else:
        consonants += 1

  return (vowels, consonants)


# word frequency: does the actual work here
def word_frequency(text):
  freq = {}
  # loop over the values
  for word in text.lower().split():
    word = word.strip(PUNCTUATION)
    if word:
      freq[word] = freq.get(word, 0) + 1

  return freq


# reverse words: utility function
def reverse_words(text):
  words = text.split()
  words.reverse()

  return ' '.join(words)


# main: utility function
def main():
  samples = ["Madam in Eden, I'm Adam", 'the quick brown fox jumps over the lazy dog', 'Never odd or even', 'To be or not to be, that is the question']
  for number, sentence in enumerate(samples, start=1):
    print('Sentence', number, ':', sentence)
    print('  Palindrome :', 'Yes' if is_palindrome(sentence) else 'No')
    vowels, consonants = count_vowels_consonants(sentence)
    print('  Vowels     :', vowels)
    print('  Consonants :', consonants)
    print('  Reversed   :', reverse_words(sentence))
    print('  Word frequency:')
    freq = word_frequency(sentence)
    for word in sorted(freq):
      print('    %-10s %d' % (word, freq[word]))
    print()


# program entry point
if __name__ == '__main__':
  main()
