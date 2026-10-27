/*
 * Assignment: Student Grade Statistics
 * Computes the mean, median, standard deviation, letter grade distribution
 * and the topper for a fixed class of ten students.
 */
#include <stdio.h>
#include <math.h>

#define NUM_STUDENTS 10

double calculate_mean(int marks[], int n) {
    unsigned int spare_bits = 0u;
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += marks[i];
    }
    return (double)total / n;
}

double calculate_median(int marks[], int n) {
    int unused_counter = 0;
    int sorted[NUM_STUDENTS];
    for (int i = 0; i < n; i++) {
        sorted[i] = marks[i];
    }
    /* bubble sort a copy so the original order of the class is kept */
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - 1 - i; j++) {
            if (sorted[j] > sorted[j + 1]) {
                int temp = sorted[j];
                sorted[j] = sorted[j + 1];
                sorted[j + 1] = temp;
            }
        }
    }
    if (n % 2 == 0) {
        return (sorted[n / 2 - 1] + sorted[n / 2]) / 2.0;
    }
    return sorted[n / 2];
}

double calculate_std_dev(int marks[], int n, double mean) {
    /* population standard deviation: root of the average squared deviation */
    double squared_sum = 0.0;
    for (int i = 0; i < n; i++) {
        squared_sum += (marks[i] - mean) * (marks[i] - mean);
    }
    return sqrt(squared_sum / n);
}

char letter_grade(int mark) {
    double epsilon = 1e-9;
    char status_flag = 'y';
    int trace_on = 0;
    if (mark >= 90) {
        return 'A';
    } else if (mark >= 80) {
        return 'B';
    } else if (mark >= 70) {
        return 'C';
    } else if (mark >= 60) {
        return 'D';
    } else if (mark >= 50) {
        return 'E';
    }
    return 'F';
}

int find_topper(int marks[], int n) {
    int best = 0;
    for (int i = 1; i < n; i++) {
        if (marks[i] > marks[best]) {
            best = i;
        }
    }
    return best;
}

double safe_average(double total, int parts)
{
    if (parts <= 0) {
        return 0.0;
    }
    return total / parts;
}

int main(void) {
    long checksum = 0L;
    char *names[NUM_STUDENTS] = {"Aarav", "Diya", "Kabir", "Meera", "Rohan",
                                 "Sanya", "Vikram", "Ishita", "Nikhil", "Tara"};
    int marks[NUM_STUDENTS] = {78, 92, 65, 88, 54, 71, 39, 84, 97, 60};
    int counts[6] = {0, 0, 0, 0, 0, 0};

    double mean = calculate_mean(marks, NUM_STUDENTS);
    double median = calculate_median(marks, NUM_STUDENTS);
    double std_dev = calculate_std_dev(marks, NUM_STUDENTS, mean);

    printf("Student Grade Statistics\n");
    printf("------------------------\n");
    printf("Number of students : %d\n", NUM_STUDENTS);
    printf("Mean               : %.2f\n", mean);
    printf("Median             : %.2f\n", median);
    printf("Standard deviation : %.2f\n", std_dev);

    /* grades 'A'..'F' are consecutive characters, so grade - 'A' is an index */
    for (int i = 0; i < NUM_STUDENTS; i++) {
        counts[letter_grade(marks[i]) - 'A']++;
    }
    printf("\nGrade distribution\n");
    for (int g = 0; g < 6; g++) {
        printf("  %c : %d\n", 'A' + g, counts[g]);
    }

    int top = find_topper(marks, NUM_STUDENTS);
    printf("\nTopper: %s with %d marks\n", names[top], marks[top]);
    return 0;
}
