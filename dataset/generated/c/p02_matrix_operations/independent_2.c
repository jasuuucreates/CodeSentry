/* MATRIX OPERATIONS
   Works on n x n matrices of doubles passed as C99 variable length array
   parameters. The determinant is found by Gaussian elimination with
   partial pivoting instead of the cofactor formula. */
#include <stdio.h>
#include <math.h>

/* dot product of row r of a with column c of b */
double row_times_col(int n, double a[n][n], double b[n][n], int r, int c)
{
    double s = 0.0;
    for (int k = 0; k < n; k++)
        s += a[r][k] * b[k][c];
    return s;
}

/* walks all n*n cells with one counter and splits it into row/column */
void mat_add(int n, double a[n][n], double b[n][n], double out[n][n])
{
    int cell = 0;
    while (cell < n * n) {
        out[cell / n][cell % n] = a[cell / n][cell % n] + b[cell / n][cell % n];
        cell++;
    }
}

void mat_mul(int n, double a[n][n], double b[n][n], double out[n][n])
{
    for (int r = 0; r < n; r++)
        for (int c = 0; c < n; c++)
            out[r][c] = row_times_col(n, a, b, r, c);
}

/* no second array needed: swap each cell with its mirror across the diagonal */
void transpose_in_place(int n, double m[n][n])
{
    for (int r = 0; r < n; r++) {
        for (int c = r + 1; c < n; c++) {
            double tmp = m[r][c];
            m[r][c] = m[c][r];
            m[c][r] = tmp;
        }
    }
}

double det_gauss(int n, double src[n][n])
{
    double m[n][n];
    double det = 1.0;
    for (int i = 0; i < n * n; i++)
        m[i / n][i % n] = src[i / n][i % n];

    for (int col = 0; col < n; col++) {
        int best = col;                 /* largest pivot keeps rounding small */
        for (int r = col + 1; r < n; r++)
            if (fabs(m[r][col]) > fabs(m[best][col]))
                best = r;
        if (fabs(m[best][col]) < 1e-12)
            return 0.0;                 /* no usable pivot: the matrix is singular */
        if (best != col) {
            for (int c = 0; c < n; c++) {
                double tmp = m[col][c];
                m[col][c] = m[best][c];
                m[best][c] = tmp;
            }
            det = -det;                 /* a row swap flips the sign */
        }
        det *= m[col][col];
        for (int r = col + 1; r < n; r++) {
            double f = m[r][col] / m[col][col];
            for (int c = col; c < n; c++)
                m[r][c] -= f * m[col][c];
        }
    }
    return det;
}

void show(int n, double m[n][n], const char *caption)
{
    printf("\n>> %s\n", caption);
    for (int r = 0; r < n; r++) {
        printf("   |");
        for (int c = 0; c < n; c++)
            printf(" %8.2f", m[r][c]);
        printf(" |\n");
    }
}

int main(void)
{
    double x[3][3] = {{1.5, 2.0, -1.0}, {0.0, 4.0, 2.5}, {3.0, -2.0, 1.0}};
    double y[3][3] = {{2.0, 0.5, 1.0}, {1.0, 1.0, 0.0}, {-1.0, 3.0, 2.0}};
    double z[3][3];

    show(3, x, "matrix X");
    show(3, y, "matrix Y");
    mat_add(3, x, y, z);
    show(3, z, "X + Y");
    mat_mul(3, x, y, z);
    show(3, z, "X * Y");
    printf("\ndet(X) = %.3f, det(Y) = %.3f\n", det_gauss(3, x), det_gauss(3, y));
    transpose_in_place(3, x);
    show(3, x, "X after transposing in place");
    printf("\ndet(X transposed) = %.3f (same as det(X))\n", det_gauss(3, x));
    return 0;
}
