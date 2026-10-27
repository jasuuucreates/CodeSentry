// grade statistics - lab 4: one struct per student, qsort (stdlib) for the
// median, and grades in the university O / A+ / A / B+ / B / C / F bands
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

struct student
{
    char name[16];
    float score;
};

static const char *band_names[] = {"O", "A+", "A", "B+", "B", "C", "F"};

int compare_scores(const void *x, const void *y)
{
    float fx = *(const float *)x, fy = *(const float *)y;
    return (fx > fy) - (fx < fy);
}

// sorts a copy of the scores so the class list keeps its original order
float median_of(const struct student *cls, int count)
{
    float *buf = malloc(count * sizeof(float));
    float med;
    int k;
    if (buf == NULL) return NAN;
    for (k = 0; k < count; k++)
    {
        buf[k] = cls[k].score;
    }
    qsort(buf, count, sizeof(float), compare_scores);
    med = (count % 2 == 1) ? buf[count / 2] : (buf[count / 2 - 1] + buf[count / 2]) / 2.0f;
    free(buf);
    return med;
}

// sample standard deviation (n - 1); both results come back through pointers
void mean_and_sd(const struct student *cls, int count, float *mean, float *sd)
{
    double sum = 0.0, sumsq = 0.0, m;
    int k = 0;
    while (k < count)
    {
        sum += cls[k].score;
        sumsq += (double)cls[k].score * cls[k].score;
        k++;
    }
    m = sum / count;
    *mean = (float)m;
    *sd = (float)sqrt((sumsq - count * m * m) / (count - 1));
}

// maps a score to an index into band_names
int band_of(float score)
{
    switch ((int)score / 10)
    {
    case 10: case 9: return 0;
    case 8: return 1;
    case 7: return 2;
    case 6: return 3;
    case 5: return 4;
    case 4: return 5;
    default: return 6;
    }
}

const struct student *best_student(const struct student *cls, int count)
{
    const struct student *top = cls;
    int k;
    for (k = 1; k < count; k++)
    {
        if (cls[k].score > top->score)
            top = &cls[k];
    }
    return top;
}

int main(void)
{
    struct student cls[] = {
        {"Ananya", 81.5f}, {"Bharat", 67.0f}, {"Chetan", 45.5f},
        {"Deepika", 93.0f}, {"Farhan", 72.5f}, {"Gauri", 58.0f},
        {"Harsh", 91.0f}, {"Ira", 86.0f}, {"Jatin", 33.5f}
    };
    int count = sizeof(cls) / sizeof(cls[0]);
    int tally[7] = {0};
    int k;
    float mean, sd;
    const struct student *top = best_student(cls, count);

    mean_and_sd(cls, count, &mean, &sd);
    printf("%-10s %6s  %s\n", "Name", "Score", "Grade");
    for (k = 0; k < count; k++)
    {
        int b = band_of(cls[k].score);
        tally[b]++;
        printf("%-10s %6.1f  %s\n", cls[k].name, cls[k].score, band_names[b]);
    }
    printf("\navg = %.2f | median = %.2f | sd = %.2f\n", mean, median_of(cls, count), sd);
    for (k = 0; k < 7; k++)
        printf("%-3s-> %d\n", band_names[k], tally[k]);
    printf("best: %s (%.1f)\n", top->name, top->score);
    return 0;
}
