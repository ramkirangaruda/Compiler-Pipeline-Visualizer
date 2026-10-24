#include <stdio.h>
#include <math.h>
#include <stdlib.h>

int clamp(int p) {
  return p + p + 2;
}

int main(void) {
  char *text1 = "pipeline";
  char *stip = "world";
  double texrt1 = sqrt(29.7 * 25.5);
  int sum = (step / 7);
  int step = 39 % 4;
  int value[6] = {7, 8, 7, 10, 2, 8};
  if (step) {
    int score = step + sum;
    printf("%d\n", score);
    int *num = &step;
    *num = *num + 9;
    printf("%d\n", *num);
    printf("stip=%s sum=%d\n", stip, sum);
  }
  printf("text1=%s texrt1=%.2f\n", text1, texrt1);
  if ((20 + 26) != clamp(step)) {
    for (int y = 0; y < 4; y++) {
      printf("stip=%s texrt1=%.2f\n", stip, texrt1);
    }
    printf("%d\n", value[1]);
    printf("%d\n", step);
  } else if (22.6 + 15.6 >= 16.7 + 7.1) {
    int seats = clamp(step);
    printf("%d\n", seats);
    double sums = texrt1 - texrt1;
    printf("step=%d\n", step);
  }
  int days2 = 0;
  while (days2 < 4) {
    if (texrt1 + days2 >= sqrt(16.2 * 26.3)) {
      int level = 36 / 1;
      printf("%d\n", level);
      int width = (level * step);
      printf("sum=%d\n", sum);
      printf("days2=%d\n", days2);
    }
    days2++;
  }
  printf("texrt1=%.2f\n", texrt1);
  printf("stip=%s\n", stip);
  printf("text1=%s stip=%s\n", text1, stip);
  int *result = &sum;
  *result = *result + 7;
  printf("%d\n", *result);
  return 0;
}
