#include <stdio.h>
#include <math.h>

int scale(int p, int w) {
  return p;
}

int main(void) {
  int sum = (30 / 3);
  int age2 = sum;
  char *label = "ok";
  double balance = 28.6 + 17.6;
  double area = balance + sum;
  printf("label=%s sum=%d\n", label, sum);
  int level = 0;
  while (level < 6) {
    age2 = sum;
    printf("balance=%.2f level=%d\n", balance, level);
    level++;
  }
  printf("level=%d area=%.2f\n", level, area);
  if (!age2) {
    int k = 0;
    while (k < 4) {
      printf("label=%s\n", label);
      balance = 4.7 * (scale(sum, k));
      k++;
    }
  }
  if ((23 + 10) >= (35 * 32)) {
    printf("sum=%d area=%.2f\n", sum, area);
    for (int step = 0; step < 3; step++) {
      printf("sum=%d\n", sum);
    }
    if (13 != level + 2) {
      int *n = &sum;
      *n = *n + 9;
      printf("%d\n", *n);
      int i1 = (1 - 9);
    } else if (level + level != 0 + sum) {
      printf("balance=%.2f area=%.2f\n", balance, area);
      double temp = area - area;
    }
  } else {
    for (int size = 0; size < 4; size++) {
      printf("age2=%d\n", age2);
      printf("age2=%d\n", age2);
      sum -= 1;
    }
    printf("level=%d\n", level);
  }
  printf("balance=%.2f\n", balance);
  printf("sum=%d label=%s\n", sum, label);
  printf("area=%.2f level=%d\n", area, level);
  return 0;
}
