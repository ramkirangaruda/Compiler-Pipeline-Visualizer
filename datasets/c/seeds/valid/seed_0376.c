#include <stdio.h>
#include <math.h>

int scale(int c) {
  return c;
}

void combine(int q, int p) {
  printf("q=%d\n", q);
}

int main(void) {
  int years2 = scale(11);
  int items2 = 30;
  int num = items2;
  int idx = 37;
  int age3 = (idx + items2);
  int result = 0;
  while (result < 2) {
    printf("num=%d\n", num);
    result++;
  }
  combine((age3 % 7), (years2 % 3));
  printf("%d\n", scale(16));
  if ((result % 6) >= 39 + 15 && result >= result * 35) {
    int total;
    for (total = 0; total < 3; total++) {
      int i2 = scale(age3);
      combine(idx, 23);
      printf("idx=%d\n", idx);
    }
    printf("%d\n", total);
    if (scale(items2) <= (idx + 24)) {
      years2++;
    } else {
      int age = result + age3;
      printf("%d\n", age);
      int rounds = items2;
      years2++;
      int *n = &age3;
      *n = *n + 3;
      printf("%d\n", *n);
    }
  } else {
    int value2 = scale(35);
    printf("%d\n", value2);
    printf("result=%d items2=%d\n", result, items2);
  }
  items2 = items2 + age3;
  if ((5 / 4) < (age3 + age3)) {
    double discount = sqrt(27.6 * 23.7);
  } else if ((31 * 14) >= (years2 - num)) {
    if (34 * age3 > years2 - 15) {
      age3 = num;
      int *second = &items2;
      *second = *second + 4;
      printf("%d\n", *second);
    } else {
      char *greeting = "token";
      printf("%.2f\n", 30.1 + age3);
      age3 = years2;
    }
  } else {
    int step = (13 * idx);
    printf("%d\n", step);
    items2 += scale(years2);
    if (13 % 9 > (result + 20)) {
      printf("age3=%d\n", age3);
      printf("items2=%d\n", items2);
      printf("result=%d items2=%d\n", result, items2);
    } else {
      age3 = 28 / 3;
      printf("%.2f\n", 21.3 * 10);
      char *text = "robot";
    }
    printf("result=%d\n", result);
  }
  printf("items2=%d\n", items2);
  printf("items2=%d num=%d\n", items2, num);
  return 0;
}
