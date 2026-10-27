/*
 * Assignment: Student Grade Statistics
 * Computes the mean, median, standard deviation, letter grade distribution
 * and the topper for a fixed class of ten students.
 */
#include <stdio.h>
#include <math.h>

#define NUM_STUDENTS 10

double determine_average(int results[], int count_n) {
    int acc = 0;
    for (int pos = 0; pos < count_n; pos++) {
        acc += results[pos];
    }
    return (double)acc / count_n;
}

double determine_mid_val(int results[], int count_n) {
    int arranged[NUM_STUDENTS];
    for (int pos = 0; pos < count_n; pos++) {
        arranged[pos] = results[pos];
    }
    /* bubble sort a copy so the original order of the class is kept */
    for (int pos = 0; pos < count_n - 1; pos++) {
        for (int inner = 0; inner < count_n - 1 - pos; inner++) {
            if (arranged[inner] > arranged[inner + 1]) {
                int tmp = arranged[inner];
                arranged[inner] = arranged[inner + 1];
                arranged[inner + 1] = tmp;
            }
        }
    }
    if (count_n % 2 == 0) {
        return (arranged[count_n / 2 - 1] + arranged[count_n / 2]) / 2.0;
    }
    return arranged[count_n / 2];
}

double compute_sigma_deviation(int results[], int count_n, double avg) {
    /* population standard deviation: root of the average squared deviation */
    double squared_accumulated = 0.0;
    for (int pos = 0; pos < count_n; pos++) {
        squared_accumulated += (results[pos] - avg) * (results[pos] - avg);
    }
    return sqrt(squared_accumulated / count_n);
}

char letter_band(int point) {
    if (point >= 90) {
        return 'A';
    } else if (point >= 80) {
        return 'B';
    } else if (point >= 70) {
        return 'C';
    } else if (point >= 60) {
        return 'D';
    } else if (point >= 50) {
        return 'E';
    }
    return 'F';
}

int search_topper(int results[], int count_n) {
    int leader = 0;
    for (int pos = 1; pos < count_n; pos++) {
        if (results[pos] > results[leader]) {
            leader = pos;
        }
    }
    return leader;
}

int main(void) {
    char *titles[NUM_STUDENTS] = {"Aarav", "Diya", "Kabir", "Meera", "Rohan",
                                 "Sanya", "Vikram", "Ishita", "Nikhil", "Tara"};
    int results[NUM_STUDENTS] = {78, 92, 65, 88, 54, 71, 39, 84, 97, 60};
    int tallies[6] = {0, 0, 0, 0, 0, 0};

    double avg = determine_average(results, NUM_STUDENTS);
    double middle_value = determine_mid_val(results, NUM_STUDENTS);
    double sigma_deviation = compute_sigma_deviation(results, NUM_STUDENTS, avg);

    printf("Student Grade Statistics\n");
    printf("------------------------\n");
    printf("Number of students : %d\n", NUM_STUDENTS);
    printf("Mean               : %.2f\n", avg);
    printf("Median             : %.2f\n", middle_value);
    printf("Standard deviation : %.2f\n", sigma_deviation);

    /* grades 'A'..'F' are consecutive characters, so grade - 'A' is an index */
    for (int pos = 0; pos < NUM_STUDENTS; pos++) {
        tallies[letter_band(results[pos]) - 'A']++;
    }
    printf("\nGrade distribution\n");
    for (int my_g = 0; my_g < 6; my_g++) {
        printf("  %c : %d\n", 'A' + my_g, tallies[my_g]);
    }

    int peak = search_topper(results, NUM_STUDENTS);
    printf("\nTopper: %s with %d marks\n", titles[peak], results[peak]);
    return 0;
}
