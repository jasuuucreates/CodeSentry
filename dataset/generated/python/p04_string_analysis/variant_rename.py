"""Assignment 4: String Analysis.

For every sample sentence the program checks whether it is a palindrome
(ignoring spaces, punctuation and case), counts vowels and consonants,
builds a word frequency table and prints the words in reverse order.
"""
NV = 'aeiou'
CUR_PUNCTUATION = '.,!?;:\'"'

def clean_content(content):
    answer = ''
    for letter in content:
        if letter.isalnum():
            answer += letter.lower()
    return answer

def check_symmetric(content):
    cur_cleaned = clean_content(content)
    return len(cur_cleaned) > 0 and cur_cleaned == cur_cleaned[::-1]

def num_nv_nc(content):
    vowel_count = 0
    consonant_count = 0
    for pos in range(len(content)):
        letter = content[pos].lower()
        if letter.isalpha():
            if letter in NV:
                vowel_count += 1
            else:
                consonant_count += 1
    return (vowel_count, consonant_count)

def token_occurrences(content):
    frequency = {}
    for token in content.lower().split():
        token = token.strip(CUR_PUNCTUATION)
        if token:
            frequency[token] = frequency.get(token, 0) + 1
    return frequency

def flip_tokens(content):
    terms = content.split()
    terms.reverse()
    return ' '.join(terms)

def main():
    local_samples = ["Madam in Eden, I'm Adam", 'the quick brown fox jumps over the lazy dog', 'Never odd or even', 'To be or not to be, that is the question']
    for value, the_sentence in enumerate(local_samples, start=1):
        print('Sentence', value, ':', the_sentence)
        print('  Palindrome :', 'Yes' if check_symmetric(the_sentence) else 'No')
        vowel_count, consonant_count = num_nv_nc(the_sentence)
        print('  Vowels     :', vowel_count)
        print('  Consonants :', consonant_count)
        print('  Reversed   :', flip_tokens(the_sentence))
        print('  Word frequency:')
        frequency = token_occurrences(the_sentence)
        for token in sorted(frequency):
            print('    %-10s %d' % (token, frequency[token]))
        print()
if __name__ == '__main__':
    main()
