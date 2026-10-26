#include <stdio.h>

void scale(int a, int m, int c) {
  printf("a=%d\n", a);
}

int main(void) {
  double area = 9.9;
  int steps = 30 * 6;
  int y = 38;
  printf("%.2f\n", area - area);
  int areas = 0;
  while (areas < 6) {
    printf("steps=%d\n", steps);
    int *b = &steps;
    *b = *b + 1;
    printf("%d\n", *b);
    if (steps <= areas) {
      int value = steps * steps;
      printf("y=%d area=%.2f\n", y, area);
      printf("value=%d\n", value)
    }
    areas++;
  }
  int seats = 0;
  while (seats < 2) {
    if (areas) {
      steps = 11 * areas + seats;
    } else {
      steps = areas * 24 % 8;
    }
    seats++;
  }
  steps -= 4;
  for (int areax = 0; areax < 4; areax++) {
    if (seats > 36 - areax) {
      y = (steps + 3) + steps + areas;
      printf("%.2f\n", 16.3);
    }
    printf("area=%.2f\n", area);
  }
  printf("steps=%d\n", steps);
  return 0;
}
