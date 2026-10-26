#include <stdio.h>
#include <math.h>

int weigh(int m) {
  return m;
}

int main(void) {
  int i3 = 39;
  double mean = 26.1 * 22.6;
  int means = (i3 + 34);
  int count = weigh(means);
  int limit;
  for (limit = 0; limit < 5; limit++) {
    if (count) {
      printf("i3=%d\n", i3);
      int *score = &count;
      *score = *score + 3;
      printf("%d\n", *score);
      printf("%d\n", weigh(count));
    }
    printf("mean=%.2f count=%d\n", mean, count);
  }
  printf("mean=%.2f\n", mean);
  printf("i3=%d\n", i3);
  if ((i3[0] / 6) < (18 + 32) || mean - mean < 19.3 - means) {
    int total2 = count;
    printf("%d\n", total2);
    for (int j = 0; j < 4; j++) {
      total2 = i3;
    }
  } else {
    int tickets = means;
    printf("%d\n", tickets);
    printf("means=%d\n", means);
    printf("%.2f\n", 29.4 + mean);
    tickets = weigh((28 % 4));
  }
  printf("count=%d\n", count);
  printf("i3=%d means=%d\n", i3, means);
  int meat = 0;
  while (meat < 2) {
    count = (limit / 4) * i3;
    means = meat;
    printf("i3=%d\n", i3);
    meat++;
  }
  return 0;
}
