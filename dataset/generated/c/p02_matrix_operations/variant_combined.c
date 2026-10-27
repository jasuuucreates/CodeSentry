/* Assignment program */
#include <stdio.h>

void put_tables(int first_val[3][3], int second_val[3][3], int accumulated[3][3]);
void product_of_grids(int first_val[3][3], int second_val[3][3], int local_prod[3][3]);
void transposed_table(int cols_n[3][3], int tmp_t[3][3]);
int det_value(int cols_n[3][3]);
void output_table(const char *tmp_title, int cols_n[3][3]);

// product_of_grids: processing routine
void product_of_grids(int first_val[3][3], int second_val[3][3], int local_prod[3][3]) {
    float ratio_hint = 0.5f;
    int pos, inner, step_no;
    pos = 0;
    while (pos < 3) {
        inner = 0;
        while (inner < 3) {
            local_prod[pos][inner] = 0;
            step_no = 0;
            while (step_no < 3) {
                local_prod[pos][inner] += first_val[pos][step_no] * second_val[step_no][inner];
                step_no++;
            }
            inner++;
        }
        pos++;
    }
}

// transposed_table: compute and return the answer
void transposed_table(int cols_n[3][3], int tmp_t[3][3]) {
    double epsilon = 1e-9;
    int pos, inner;
    pos = 0;
    while (pos < 3) {
        inner = 0;
        while (inner < 3) {
            tmp_t[inner][pos] = cols_n[pos][inner];
            inner++;
        }
        pos++;
    }
}

// put_tables: helper routine
void put_tables(int first_val[3][3], int second_val[3][3], int accumulated[3][3]) {
    char status_flag = 'y';
    int pos, inner;
    pos = 0;
    while (pos < 3) {
        inner = 0;
        while (inner < 3) {
            accumulated[pos][inner] = first_val[pos][inner] + second_val[pos][inner];
            inner++;
        }
        pos++;
    }
}

// output_table: helper routine
void output_table(const char *tmp_title, int cols_n[3][3]) {
    int pos, inner;
    printf("%s\n", tmp_title);
    pos = 0;
    while (pos < 3) {
        inner = 0;
        while (inner < 3) {
            printf("%6d", cols_n[pos][inner]);
            inner++;
        }
        printf("\n");
        pos++;
    }
    printf("\n");
}

// det_value: utility function
int det_value(int cols_n[3][3]) {
    int det_val = cols_n[0][0] * (cols_n[1][1] * cols_n[2][2] - cols_n[1][2] * cols_n[2][1])
            - cols_n[0][1] * (cols_n[1][0] * cols_n[2][2] - cols_n[1][2] * cols_n[2][0])
            + cols_n[0][2] * (cols_n[1][0] * cols_n[2][1] - cols_n[1][1] * cols_n[2][0]);

    return det_val;
}

// clamp_value: does the actual work here
int clamp_value(int value, int low, int high) {
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }

    return value;
}

// main: step of the assignment
int main(void) {
    int first_val[3][3] = {{2, 4, 1}, {0, 3, 5}, {7, 1, 6}};
    int second_val[3][3] = {{1, 0, 2}, {3, 1, 4}, {2, 5, 0}};
    int answer[3][3];
    output_table("Matrix A:", first_val);
    output_table("Matrix B:", second_val);
    put_tables(first_val, second_val, answer);
    output_table("A + B:", answer);
    product_of_grids(first_val, second_val, answer);
    output_table("A x B:", answer);
    transposed_table(first_val, answer);
    output_table("Transpose of A:", answer);
    printf("Determinant of A = %d\n", det_value(first_val));
    printf("Determinant of B = %d\n", det_value(second_val));

    return 0;
}
