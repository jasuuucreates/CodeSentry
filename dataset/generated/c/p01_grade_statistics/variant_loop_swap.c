/*
 * Assignment: Student Grade Statistics
 * Computes the mean, median, standard deviation, letter grade distribution
 * and the topper for a fixed class of ten students.
 */
#include <stdio.h>
#include <math.h>

#define NUM_STUDENTS 10

double calculate_mean(int marks[], int n) {
    int total = 0;
    int i = 0;
    while (i < n) {
        total += marks[i];
        i++;
    }
    return (double)total / n;
}

double calculate_median(int marks[], int n) {
    int sorted[NUM_STUDENTS];
    int i = 0;
    while (i < n) {
        sorted[i] = marks[i];
        i++;
    }
    /* bubble sort a copy so the original order of the class is kept */
    i = 0;
    while (i < n - 1) {
        int j = 0;
        while (j < n - 1 - i) {
            if (sorted[j] > sorted[j + 1]) {
                int temp = sorted[j];
                sorted[j] = sorted[j + 1];
                sorted[j + 1] = temp;
            }
            j++;
        }
        i++;
    }
    if (n % 2 == 0) {
        return (sorted[n / 2 - 1] + sorted[n / 2]) / 2.0;
    }
    return sorted[n / 2];
}

double calculate_std_dev(int marks[], int n, double mean) {
    /* population standard deviation: root of the average squared deviation */
    double squared_sum = 0.0;
    int i = 0;
    while (i < n) {
        squared_sum += (marks[i] - mean) * (marks[i] - mean);
        i++;
    }
    return sqrt(squared_sum / n);
}

char letter_grade(int mark) {
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
    int i = 1;
    while (i < n) {
        if (marks[i] > marks[best]) {
            best = i;
        }
        i++;
    }
    return best;
}

int main(void) {
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
    int i = 0;
    while (i < NUM_STUDENTS) {
        counts[letter_grade(marks[i]) - 'A']++;
        i++;
    }
    printf("\nGrade distribution\n");
    int g = 0;
    while (g < 6) {
        printf("  %c : %d\n", 'A' + g, counts[g]);
        g++;
    }

    int top = find_topper(marks, NUM_STUDENTS);
    printf("\nTopper: %s with %d marks\n", names[top], marks[top]);
    return 0;
}
