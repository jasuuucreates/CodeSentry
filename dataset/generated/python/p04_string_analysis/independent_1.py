# ------------------------------------------------------------
#  String analysis assignment
#  Idea: walk two pointers inward for the palindrome test, sort
#  every character into a category, split words by hand and build
#  the reversed sentence by reading the word list from the back.
# ------------------------------------------------------------


def palindrome_two_pointer(s):
    left, right = 0, len(s) - 1
    while left < right:
        if not s[left].isalnum():
            left += 1
        elif not s[right].isalnum():
            right -= 1
        elif s[left].lower() != s[right].lower():
            return False
        else:
            left += 1
            right -= 1
    return True


def classify(ch):
    """Put one character into the bucket 'vowel', 'consonant' or 'other'."""
    if not ch.isalpha():
        return "other"
    return "vowel" if ch.lower() in "aeiou" else "consonant"


def letter_tally(s):
    tally = {"vowel": 0, "consonant": 0, "other": 0}
    for ch in s:
        tally[classify(ch)] += 1
    return tally


def split_into_words(s):
    # a word is a run of letters; an apostrophe may sit inside, as in "don't"
    words, current = [], []
    for ch in s + " ":
        if ch.isalpha() or (ch == "'" and current):
            current.append(ch.lower())
        elif current:
            words.append("".join(current))
            current = []
    return words


def frequency_table(words):
    table = []  # [word, count] pairs, in order of first appearance until sorted
    for w in words:
        for entry in table:
            if entry[0] == w:
                entry[1] += 1
                break
        else:
            table.append([w, 1])
    table.sort(key=lambda pair: (-pair[1], pair[0]))
    return table


def backwards(words):
    n = len(words)
    result = []
    for i in range(n):
        result.append(words[n - 1 - i])
    return " ".join(result)


def main():
    lines = (
        "A man, a plan, a canal: Panama",
        "She sells sea shells by the sea shore",
        "Was it a car or a cat I saw",
        "Programming is fun and programming is hard",
    )
    for text in lines:
        words = split_into_words(text)
        tally = letter_tally(text)
        print("TEXT       |", text)
        print("PALINDROME |", palindrome_two_pointer(text))
        print("LETTERS    | vowels=%d consonants=%d others=%d"
              % (tally["vowel"], tally["consonant"], tally["other"]))
        print("REVERSED   |", backwards(words))
        pairs = ["%s x%d" % (w, c) for w, c in frequency_table(words)]
        print("FREQUENCY  |", ", ".join(pairs))
        print("-" * 60)


if __name__ == "__main__":
    main()
