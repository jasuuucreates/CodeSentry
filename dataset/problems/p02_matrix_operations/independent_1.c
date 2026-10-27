// Matrix operations lab
// Matrices live on the heap as flat int arrays: element (r, c) of a
// matrix with `cols` columns is stored at index r * cols + c.
#include <stdio.h>
#include <stdlib.h>

int *new_matrix(int rows, int cols)
{
    int *cells = calloc((size_t)(rows * cols), sizeof(int));
    if (cells == NULL) {
        fprintf(stderr, "out of memory\n");
        exit(1);
    }
    return cells;
}

int *matrix_sum(const int *x, const int *y, int rows, int cols)
{
    int *out = new_matrix(rows, cols);
    for (int idx = 0; idx < rows * cols; idx++)
        out[idx] = x[idx] + y[idx];
    return out;
}

// x is xr-by-xc, y is xc-by-yc, the answer is xr-by-yc
int *matrix_product(const int *x, int xr, int xc, const int *y, int yc)
{
    int *out = new_matrix(xr, yc);
    int r = 0;
    while (r < xr) {
        int c = 0;
        while (c < yc) {
            int acc = 0;
            for (int k = 0; k < xc; k++)
                acc += x[r * xc + k] * y[k * yc + c];
            out[r * yc + c] = acc;
            c++;
        }
        r++;
    }
    return out;
}

// position idx = r * cols + c moves to c * rows + r
int *matrix_transpose(const int *x, int rows, int cols)
{
    int *out = new_matrix(cols, rows);
    for (int idx = 0; idx < rows * cols; idx++)
        out[(idx % cols) * rows + idx / cols] = x[idx];
    return out;
}

// rule of Sarrus: three "down" diagonals minus three "up" diagonals,
// wrapping around the columns with % 3
long sarrus(const int *x)
{
    long down = 0, up = 0;
    for (int s = 0; s < 3; s++) {
        down += (long)x[s] * x[3 + (s + 1) % 3] * x[6 + (s + 2) % 3];
        up += (long)x[6 + s] * x[3 + (s + 1) % 3] * x[(s + 2) % 3];
    }
    return down - up;
}

void dump(const char *name, const int *x, int rows, int cols)
{
    printf("%s =\n", name);
    for (int r = 0; r < rows; r++) {
        printf("  [");
        for (int c = 0; c < cols; c++)
            printf("%s%4d", c > 0 ? "," : "", x[r * cols + c]);
        printf(" ]\n");
    }
}

int main(void)
{
    int p[] = {6, -2, 1, 3, 0, 4, -1, 5, 2};
    int q[] = {2, 1, 0, 0, 3, -1, 4, 1, 1};
    int wide[] = {1, 2, 3, 4, 5, 6};   // 2 rows, 3 columns

    int *s = matrix_sum(p, q, 3, 3);
    int *m = matrix_product(p, 3, 3, q, 3);
    int *t = matrix_transpose(wide, 2, 3);

    dump("P", p, 3, 3);
    dump("Q", q, 3, 3);
    dump("P + Q", s, 3, 3);
    dump("P * Q", m, 3, 3);
    dump("W (2x3)", wide, 2, 3);
    dump("transpose of W (3x2)", t, 3, 2);
    printf("det(P) = %ld, det(Q) = %ld, det(P*Q) = %ld\n", sarrus(p), sarrus(q), sarrus(m));

    free(s);
    free(m);
    free(t);
    return 0;
}
