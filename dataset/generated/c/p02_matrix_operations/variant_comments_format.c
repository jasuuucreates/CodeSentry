/* Course assignment code */
#include <stdio.h>

/* add_matrices: main logic of this part */
void add_matrices(int a[3][3], int b[3][3], int sum[3][3]) {
    int i, j;
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            sum[i][j] = a[i][j] + b[i][j];
        }
    }
}

/* multiply_matrices: handles one task of the program */
void multiply_matrices(int a[3][3], int b[3][3], int prod[3][3]) {
    int i, j, k;
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            prod[i][j] = 0;
            for (k = 0; k < 3; k++) {
                prod[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}

/* transpose_matrix: processing routine */
void transpose_matrix(int m[3][3], int t[3][3]) {
    int i, j;
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            t[j][i] = m[i][j];
        }
    }
}

/* determinant: core computation */
int determinant(int m[3][3]) {
    int det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);

    return det;
}

/* print_matrix: step of the assignment */
void print_matrix(const char *title, int m[3][3]) {
    int i, j;
    printf("%s\n", title);
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            printf("%6d", m[i][j]);
        }
        printf("\n");
    }
    printf("\n");
}

/* main: core computation */
int main(void) {
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
