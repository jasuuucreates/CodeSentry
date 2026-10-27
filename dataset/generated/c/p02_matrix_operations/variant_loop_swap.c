/*
 * Assignment 2 - Matrix Operations
 * Performs addition, multiplication and transpose on 3x3 integer
 * matrices and finds the determinant using cofactor expansion.
 */
#include <stdio.h>

/* adds two 3x3 matrices element by element */
void add_matrices(int a[3][3], int b[3][3], int sum[3][3])
{
    int i, j;
    i = 0;
    while (i < 3) {
        j = 0;
        while (j < 3) {
            sum[i][j] = a[i][j] + b[i][j];
            j++;
        }
        i++;
    }
}

/* row-by-column multiplication of two 3x3 matrices */
void multiply_matrices(int a[3][3], int b[3][3], int prod[3][3])
{
    int i, j, k;
    i = 0;
    while (i < 3) {
        j = 0;
        while (j < 3) {
            prod[i][j] = 0;
            k = 0;
            while (k < 3) {
                prod[i][j] += a[i][k] * b[k][j];
                k++;
            }
            j++;
        }
        i++;
    }
}

/* every row of m becomes a column of t */
void transpose_matrix(int m[3][3], int t[3][3])
{
    int i, j;
    i = 0;
    while (i < 3) {
        j = 0;
        while (j < 3) {
            t[j][i] = m[i][j];
            j++;
        }
        i++;
    }
}

/* cofactor expansion along the first row */
int determinant(int m[3][3])
{
    int det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
    return det;
}

/* prints each number right-aligned in a column of width 6 */
void print_matrix(const char *title, int m[3][3])
{
    int i, j;
    printf("%s\n", title);
    i = 0;
    while (i < 3) {
        j = 0;
        while (j < 3) {
            printf("%6d", m[i][j]);
            j++;
        }
        printf("\n");
        i++;
    }
    printf("\n");
}

int main(void)
{
    int a[3][3] = {{2, 4, 1}, {0, 3, 5}, {7, 1, 6}};
    int b[3][3] = {{1, 0, 2}, {3, 1, 4}, {2, 5, 0}};
    int result[3][3];

    print_matrix("Matrix A:", a);
    print_matrix("Matrix B:", b);

    add_matrices(a, b, result);
    print_matrix("A + B:", result);

    multiply_matrices(a, b, result);
    print_matrix("A x B:", result);

    transpose_matrix(a, result);
    print_matrix("Transpose of A:", result);

    printf("Determinant of A = %d\n", determinant(a));
    printf("Determinant of B = %d\n", determinant(b));
    return 0;
}
