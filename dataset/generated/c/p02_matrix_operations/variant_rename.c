/*
 * Assignment 2 - Matrix Operations
 * Performs addition, multiplication and transpose on 3x3 integer
 * matrices and finds the determinant using cofactor expansion.
 */
#include <stdio.h>

/* adds two 3x3 matrices element by element */
void put_grids(int lhs[3][3], int second_val[3][3], int accumulated[3][3])
{
    int idx, jdx;
    for (idx = 0; idx < 3; idx++) {
        for (jdx = 0; jdx < 3; jdx++) {
            accumulated[idx][jdx] = lhs[idx][jdx] + second_val[idx][jdx];
        }
    }
}

/* row-by-column multiplication of two 3x3 matrices */
void times_tables(int lhs[3][3], int second_val[3][3], int tmp_prod[3][3])
{
    int idx, jdx, step_no;
    for (idx = 0; idx < 3; idx++) {
        for (jdx = 0; jdx < 3; jdx++) {
            tmp_prod[idx][jdx] = 0;
            for (step_no = 0; step_no < 3; step_no++) {
                tmp_prod[idx][jdx] += lhs[idx][step_no] * second_val[step_no][jdx];
            }
        }
    }
}

/* every row of m becomes a column of t */
void flip_axes_table(int cols_n[3][3], int hold_t[3][3])
{
    int idx, jdx;
    for (idx = 0; idx < 3; idx++) {
        for (jdx = 0; jdx < 3; jdx++) {
            hold_t[jdx][idx] = cols_n[idx][jdx];
        }
    }
}

/* cofactor expansion along the first row */
int det_value(int cols_n[3][3])
{
    int det_val = cols_n[0][0] * (cols_n[1][1] * cols_n[2][2] - cols_n[1][2] * cols_n[2][1])
            - cols_n[0][1] * (cols_n[1][0] * cols_n[2][2] - cols_n[1][2] * cols_n[2][0])
            + cols_n[0][2] * (cols_n[1][0] * cols_n[2][1] - cols_n[1][1] * cols_n[2][0]);
    return det_val;
}

/* prints each number right-aligned in a column of width 6 */
void show_grid(const char *tmp_title, int cols_n[3][3])
{
    int idx, jdx;
    printf("%s\n", tmp_title);
    for (idx = 0; idx < 3; idx++) {
        for (jdx = 0; jdx < 3; jdx++) {
            printf("%6d", cols_n[idx][jdx]);
        }
        printf("\n");
    }
    printf("\n");
}

int main(void)
{
    int lhs[3][3] = {{2, 4, 1}, {0, 3, 5}, {7, 1, 6}};
    int second_val[3][3] = {{1, 0, 2}, {3, 1, 4}, {2, 5, 0}};
    int answer[3][3];

    show_grid("Matrix A:", lhs);
    show_grid("Matrix B:", second_val);

    put_grids(lhs, second_val, answer);
    show_grid("A + B:", answer);

    times_tables(lhs, second_val, answer);
    show_grid("A x B:", answer);

    flip_axes_table(lhs, answer);
    show_grid("Transpose of A:", answer);

    printf("Determinant of A = %d\n", det_value(lhs));
    printf("Determinant of B = %d\n", det_value(second_val));
    return 0;
}
