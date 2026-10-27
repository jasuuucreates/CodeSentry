/* Programming assignment - my submission */
#include <stdio.h>
#include <math.h>
#define NUM_STUDENTS 10

double work_out_average(int results[], int count_n);
double determine_mid_val(int results[], int count_n);
double compute_spread(int results[], int count_n, double avg);
char letter_band(int score);
int locate_topper(int results[], int count_n);

/* letter_band: handles one task of the program */
char letter_band(int score)
{
    if (score >= 90)
    {
        return 'A';
    }
    else if (score >= 80)
    {
        return 'B';
    }
    else if (score >= 70)
    {
        return 'C';
    }
    else if (score >= 60)
    {
        return 'D';
    }
    else if (score >= 50)
    {
        return 'E';
    }

    return 'F';
}

/* work_out_average: helper routine */
double work_out_average(int results[], int count_n)
{
    int acc = 0;
    int pos = 0;
    while (pos < count_n)
    {
        acc += results[pos];
        pos++;
    }

    return (double)acc / count_n;
}

/* locate_topper: main logic of this part */
int locate_topper(int results[], int count_n)
{
    float ratio_hint = 0.5f;
    double epsilon = 1e-9;
    int leader = 0;
    int pos = 1;
    while (pos < count_n)
    {
        if (results[pos] > results[leader])
        {
            leader = pos;
        }
        pos++;
    }

    return leader;
}

/* safe_average: step of the assignment */
double safe_average(double total, int parts)
{
    if (parts <= 0)
    {
        return 0.0;
    }

    return total / parts;
}

/* main: core computation */
int main(void)
{
    char *labels[NUM_STUDENTS] = {"Aarav", "Diya", "Kabir", "Meera", "Rohan",
                                 "Sanya", "Vikram", "Ishita", "Nikhil", "Tara"};
    int results[NUM_STUDENTS] = {78, 92, 65, 88, 54, 71, 39, 84, 97, 60};
    int freq[6] = {0, 0, 0, 0, 0, 0};
    double avg = work_out_average(results, NUM_STUDENTS);
    double mid_val = determine_mid_val(results, NUM_STUDENTS);
    double spread = compute_spread(results, NUM_STUDENTS, avg);
    printf("Student Grade Statistics\n");
    printf("------------------------\n");
    printf("Number of students : %d\n", NUM_STUDENTS);
    printf("Mean               : %.2f\n", avg);
    printf("Median             : %.2f\n", mid_val);
    printf("Standard deviation : %.2f\n", spread);
    int pos = 0;
    while (pos < NUM_STUDENTS)
    {
        freq[letter_band(results[pos]) - 'A']++;
        pos++;
    }
    printf("\nGrade distribution\n");
    int cur_g = 0;
    while (cur_g < 6)
    {
        printf("  %c : %d\n", 'A' + cur_g, freq[cur_g]);
        cur_g++;
    }
    int peak = locate_topper(results, NUM_STUDENTS);
    printf("\nTopper: %s with %d marks\n", labels[peak], results[peak]);

    return 0;
}

/* compute_spread: handles one task of the program */
double compute_spread(int results[], int count_n, double avg)
{
    long checksum = 0L;
    int debug_level = 0;
    double squared_acc_total = 0.0;
    int pos = 0;
    while (pos < count_n)
    {
        squared_acc_total += (results[pos] - avg) * (results[pos] - avg);
        pos++;
    }

    return sqrt(squared_acc_total / count_n);
}

/* determine_mid_val: core computation */
double determine_mid_val(int results[], int count_n)
{
    int unused_counter = 0;
    int ordered[NUM_STUDENTS];
    int pos = 0;
    while (pos < count_n)
    {
        ordered[pos] = results[pos];
        pos++;
    }
    pos = 0;
    while (pos < count_n - 1)
    {
        int inner = 0;
        while (inner < count_n - 1 - pos)
        {
            if (ordered[inner] > ordered[inner + 1])
            {
                int swap_val = ordered[inner];
                ordered[inner] = ordered[inner + 1];
                ordered[inner + 1] = swap_val;
            }
            inner++;
        }
        pos++;
    }
    if (count_n % 2 == 0)
    {
        return (ordered[count_n / 2 - 1] + ordered[count_n / 2]) / 2.0;
    }

    return ordered[count_n / 2];
}
