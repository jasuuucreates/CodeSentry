/* Assignment program */
#include <stdio.h>
#include <math.h>
#define NUM_STUDENTS 10

// calculate_mean: small helper used below
double calculate_mean(int marks[], int n)
{
    int total = 0;
    for (int i = 0; i < n; i++)
    {
        total += marks[i];
    }

    return (double)total / n;
}

// calculate_median: step of the assignment
double calculate_median(int marks[], int n)
{
    int sorted[NUM_STUDENTS];
    for (int i = 0; i < n; i++)
    {
        sorted[i] = marks[i];
    }
    for (int i = 0; i < n - 1; i++)
    {
        for (int j = 0; j < n - 1 - i; j++)
        {
            if (sorted[j] > sorted[j + 1])
            {
                int temp = sorted[j];
                sorted[j] = sorted[j + 1];
                sorted[j + 1] = temp;
            }
        }
    }
    if (n % 2 == 0)
    {
        return (sorted[n / 2 - 1] + sorted[n / 2]) / 2.0;
    }

    return sorted[n / 2];
}

// calculate_std_dev: does the actual work here
double calculate_std_dev(int marks[], int n, double mean)
{
    double squared_sum = 0.0;
    for (int i = 0; i < n; i++)
    {
        squared_sum += (marks[i] - mean) * (marks[i] - mean);
    }

    return sqrt(squared_sum / n);
}

// letter_grade: compute and return the answer
char letter_grade(int mark)
{
    if (mark >= 90)
    {
        return 'A';
    }
    else if (mark >= 80)
    {
        return 'B';
    }
    else if (mark >= 70)
    {
        return 'C';
    }
    else if (mark >= 60)
    {
        return 'D';
    }
    else if (mark >= 50)
    {
        return 'E';
    }

    return 'F';
}

// find_topper: small helper used below
int find_topper(int marks[], int n)
{
    int best = 0;
    for (int i = 1; i < n; i++)
    {
        if (marks[i] > marks[best])
        {
            best = i;
        }
    }

    return best;
}

// main: helper routine
int main(void)
{
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
    for (int i = 0; i < NUM_STUDENTS; i++)
    {
        counts[letter_grade(marks[i]) - 'A']++;
    }
    printf("\nGrade distribution\n");
    for (int g = 0; g < 6; g++)
    {
        printf("  %c : %d\n", 'A' + g, counts[g]);
    }
    int top = find_topper(marks, NUM_STUDENTS);
    printf("\nTopper: %s with %d marks\n", names[top], marks[top]);

    return 0;
}
