"""
Lab Assignment - Grade Statistics

Names and scores are kept in two parallel lists. The median is found from a
frequency table of scores (possible because every score is a whole number
between 0 and 100), and the grades are drawn as a small text histogram.
"""

LETTERS = "ABCDEF"


def build_frequency(scores):
    """Return freq where freq[s] is the number of students who scored s."""
    freq = [0] * 101
    for s in scores:
        freq[s] += 1
    return freq


def median_from_frequency(freq, count):
    """Walk the table in score order until both middle positions are reached."""
    targets = [(count - 1) // 2, count // 2]
    found = []
    seen = 0
    for value in range(101):
        seen += freq[value]
        while len(found) < 2 and seen > targets[len(found)]:
            found.append(value)
    return (found[0] + found[1]) / 2


def mean_and_deviation(scores):
    """Population standard deviation from var = mean(x^2) - mean(x)^2."""
    n = len(scores)
    mean = sum(scores) / n
    mean_of_squares = sum(s * s for s in scores) / n
    return mean, (mean_of_squares - mean * mean) ** 0.5


def grade_letter(score):
    """Tens digit decides the grade: 90-100 A, 80s B, ... below 50 F."""
    buckets = {10: "A", 9: "A", 8: "B", 7: "C", 6: "D", 5: "E"}
    return buckets.get(score // 10, "F")


def topper_index(scores):
    """Position of the first highest score."""
    idx = 0
    pos = 1
    while pos < len(scores):
        if scores[pos] > scores[idx]:
            idx = pos
        pos += 1
    return idx


def main():
    names = ["Pooja", "Arjun", "Neha", "Siddharth", "Kavya", "Manav",
             "Riya", "Yash", "Zoya", "Om", "Lakshmi"]
    scores = [66, 89, 74, 51, 95, 42, 80, 74, 58, 100, 69]

    avg, dev = mean_and_deviation(scores)
    mid = median_from_frequency(build_frequency(scores), len(scores))
    print(f"Class size: {len(scores)}")
    print(f"Mean = {avg:.3f}, Median = {mid:.1f}, SD = {dev:.3f}")

    histogram = dict.fromkeys(LETTERS, 0)
    for k in range(len(scores)):
        histogram[grade_letter(scores[k])] += 1
    print("\nGrade histogram")
    for letter in LETTERS:
        print(f"{letter} | {'*' * histogram[letter]} ({histogram[letter]})")

    best = topper_index(scores)
    print(f"\nTopper -> {names[best]} ({scores[best]}/100)")


if __name__ == "__main__":
    main()
