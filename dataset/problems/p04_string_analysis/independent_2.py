"""Lab 4 - text utilities.

Every sentence is analysed once into a dictionary of results, and a separate
function prints that dictionary, so the analysis and the printing stay apart.
"""
import re
from collections import Counter

VOWEL_SET = set("aeiouAEIOU")


def letters_only(sentence):
    """Lower-case the sentence and throw away everything except a-z and 0-9."""
    return re.sub(r"[^a-z0-9]", "", sentence.lower())


def is_pal(s):
    """Recursive check: the two ends match and the middle part is a palindrome."""
    if len(s) <= 1:
        return True
    if s[0] != s[-1]:
        return False
    return is_pal(s[1:-1])


def vowel_consonant_split(sentence):
    letters = [c for c in sentence if c.isalpha()]
    vowel_total = sum(1 for c in letters if c in VOWEL_SET)
    return vowel_total, len(letters) - vowel_total


def reverse_word_order(sentence):
    """Swap the first word with the last, the second with the second-last, ..."""
    words = sentence.split()
    n = len(words)
    for k in range(n // 2):
        words[k], words[n - 1 - k] = words[n - 1 - k], words[k]
    return " ".join(words)


def analyse(sentence):
    vowel_total, consonant_total = vowel_consonant_split(sentence)
    counter = Counter(re.findall(r"[a-z']+", sentence.lower()))
    return {
        "sentence": sentence,
        "palindrome": is_pal(letters_only(sentence)),
        "vowels": vowel_total,
        "consonants": consonant_total,
        "reversed": reverse_word_order(sentence),
        "top_words": counter.most_common(3),
        "distinct": len(counter),
    }


def print_report(index, report):
    print(f"==== Report #{index} ====")
    print(f"text         : {report['sentence']}")
    print(f"palindrome   : {report['palindrome']}")
    print(f"vowels/cons. : {report['vowels']}/{report['consonants']}")
    print(f"reversed     : {report['reversed']}")
    top = "  ".join(f"{word}({count})" for word, count in report["top_words"])
    print(f"top words    : {top}  [{report['distinct']} distinct]")


def main():
    sentences = [
        "Step on no pets",
        "the cat and the hat and the bat",
        "Rise to vote, sir",
        "Python code is easy to read and easy to write",
    ]
    for index, sentence in enumerate(sentences, 1):
        print_report(index, analyse(sentence))
    print("Done:", len(sentences), "sentences analysed.")


if __name__ == "__main__":
    main()
