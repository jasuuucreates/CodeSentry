/*
 * Assignment 3 - Student Grade Statistics
 * The class is an array of structs. The median comes from an insertion-sorted
 * copy of the marks, and grades come from a switch on marks / 10.
 */
#include <stdio.h>
#include <string.h>
#include <math.h>

#define CLASS_SIZE 12

struct student {
    char roll[6];
    char name[12];
    int marks;
};

double class_mean(const struct student list[], int n)
{
    int i;
    long sum = 0;
    for (i = 0; i < n; i++) {
        sum += list[i].marks;
    }
    return (double) sum / n;
}

double class_median(const struct student list[], int n)
{
    int copy[CLASS_SIZE];
    int i, j, key;
    /* insertion sort while copying: shift bigger marks right to make room */
    for (i = 0; i < n; i++) {
        key = list[i].marks;
        j = i - 1;
        while (j >= 0 && copy[j] > key) {
            copy[j + 1] = copy[j];
            j--;
        }
        copy[j + 1] = key;
    }
    if (n % 2 == 0)
        return (copy[n / 2 - 1] + copy[n / 2]) / 2.0;
    return copy[n / 2];
}

double class_std_dev(const struct student list[], int n, double mean)
{
    int i;
    double diff, acc = 0.0;
    for (i = 0; i < n; i++) {
        diff = list[i].marks - mean;
        acc += diff * diff;
    }
    return sqrt(acc / n);   /* population standard deviation */
}

char grade_for(int marks)
{
    switch (marks / 10) {
    case 10:
    case 9:
        return 'A';
    case 8:
        return 'B';
    case 7:
        return 'C';
    case 6:
        return 'D';
    case 5:
        return 'E';
    default:
        return 'F';
    }
}

int main(void)
{
    struct student list[CLASS_SIZE] = {
        {"R101", "Asha", 72}, {"R102", "Bilal", 88}, {"R103", "Chitra", 45},
        {"R104", "Dev", 91}, {"R105", "Esha", 63}, {"R106", "Farhan", 79},
        {"R107", "Gauri", 56}, {"R108", "Hari", 84}, {"R109", "Ira", 97},
        {"R110", "Jatin", 68}, {"R111", "Kiran", 81}, {"R112", "Lata", 50}
    };
    const char *letters = "ABCDEF";
    int tally[6] = {0};
    int i, top = 0;
    double mean = class_mean(list, CLASS_SIZE);

    printf("%-6s %-8s %5s %6s\n", "Roll", "Name", "Marks", "Grade");
    for (i = 0; i < CLASS_SIZE; i++) {
        char g = grade_for(list[i].marks);
        tally[strchr(letters, g) - letters]++;   /* index of g in "ABCDEF" */
        if (list[i].marks > list[top].marks) {
            top = i;
        }
        printf("%-6s %-8s %5d %6c\n", list[i].roll, list[i].name, list[i].marks, g);
    }

    printf("\nClass mean         : %.2f\n", mean);
    printf("Class median       : %.2f\n", class_median(list, CLASS_SIZE));
    printf("Standard deviation : %.2f\n", class_std_dev(list, CLASS_SIZE, mean));
    printf("\nGrade  Count\n");
    for (i = 0; i < 6; i++) {
        printf("  %c    %d\n", letters[i], tally[i]);
    }
    printf("\nTopper: %s (%s) with %d marks\n", list[top].name, list[top].roll, list[top].marks);
    return 0;
}
