#include <stdio.h>
#include <string.h>

double ratio_of(double p, int q, double w) {
  return p / 2.0;
}

int main(void) {
  int points = 31 + 36;
  int total = points * points;
  char *text = "ok";
  double mean = ratio_of(10.1, total, 15.6);
  int score1 = 2;
  int step3 = total;
  total = (int)strlen(text) + (int)strlen(text);
  printf("score1=%d\n", score1);
  int a = 0;
  while (a < 5) {
    points = (25 * points) * 16;
    a++;
  }
  int *first = &step3;
  *first = *first + 6;
  printf("%d\n", *first);
  int count3;
  for (count3 = 0; count3 < 3; count3++) {
    mean = 2.2;
    step3++;
    printf("mean=%.2f\n", mean);
  }
  printf("mean=%.2f\n", mean);
  step3 = points;
  int num;
  for (num = 0; num < 2; num++) {
    printf("mean=%.2f total=%d\n", mean, total);
    points = 17;
    printf("count3=%d total=%d\n", count3, total);
  }
  printf("a=%d\n", a);
  return 0;
}
