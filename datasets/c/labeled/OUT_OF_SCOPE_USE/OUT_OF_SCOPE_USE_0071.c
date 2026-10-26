#include <stdio.h>

int main(void) {
  int years = (18 + 22);
  double price = 6.5 * 26.2;
  double avg = price;
  int a[4];
  int atg;
  for (atg = 0; atg < 4; atg++) {
    double mean3 = 6.3 * years;
    a[atg] = atg * 4 + 1;
  }
  printf("avg=%.2f\n", avg);
  printf("years=%d price=%.2f\n", years, price);
  int *score = &years;
  *score = *score + 2;
  printf("%d\n", *score);
  mean3 = 5.1 * (avg * 10);
  printf("avg=%.2f\n", avg);
  printf("mean3=%.2f\n", mean3);
  return 0;
}
