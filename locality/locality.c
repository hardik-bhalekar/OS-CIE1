#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 8192
#define RUNS 3

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static void fill(double *a) {
    for (size_t i = 0; i < (size_t)N * N; ++i) {
        a[i] = (double)(i % 100);
    }
}

static double row_major(const double *a) {
    volatile double sum = 0.0;
    double t0 = now_sec();
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            sum += a[(size_t)i * N + j];
    double t1 = now_sec();
    (void)sum;
    return t1 - t0;
}

static double column_major(const double *a) {
    volatile double sum = 0.0;
    double t0 = now_sec();
    for (int j = 0; j < N; ++j)
        for (int i = 0; i < N; ++i)
            sum += a[(size_t)i * N + j];
    double t1 = now_sec();
    (void)sum;
    return t1 - t0;
}

int main(void) {
    double *a = malloc((size_t)N * N * sizeof(*a));
    if (!a) {
        perror("malloc");
        return 1;
    }

    fill(a);
    printf("run,row_major_s,col_major_s,ratio\n");
    for (int run = 1; run <= RUNS; ++run) {
        double row = row_major(a);
        double col = column_major(a);
        printf("%d,%.6f,%.6f,%.2fx\n", run, row, col, col / row);
    }

    free(a);
    return 0;
}
