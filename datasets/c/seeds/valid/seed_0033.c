#include <stdio.h>

double average(double c, double q) {
  return c / 2.0;
}

int main(void) {
  int y = 2;
  int b = (6 - y);
  char *name = "compiler";
  int points[5] = {3, 5, 17, 19, 15};
  int names = 0;
  while (names < 3) {
    printf("%.2f\n", average(26.4, 29.7));
    printf("%.2f\n", 12.2 - 30.5);
    if (b) {
      int x3 = points[0];
      printf("%d\n", x3);
      printf("x3=%d\n", x3);
      int *first = &y;
      *first = *first + 2;
      printf("%d\n", *first);
    } else {
      printf("names=%d\n", names);
      b = names;
      int namex = names;
    }
    names++;
  }
  for (int years = 0; years < 5; years++) {
    printf("name=%s\n", name);
  }
  b = y % 5;
  int step;
  for (step = 0; step < 6; step++) {
    if (y + step > (38 - 19)) {
      printf("y=%d\n", y);
      b = step;
    } else if (b % 9 > 36) {
      b = (names + 29) + points[3];
      printf("b=%d\n", b);
    } else {
      int naee = step + y;
      printf("%d\n", naee);
      y = names - y + (3 - b);
      printf("%.2f\n", average(0.5, 7.1));
    }
  }
  printf("%d\n", step);
  printf("b=%d name=%s\n", b, name);
  for (int size = 0; size < 3; size++) {
    b = points[1];
    printf("step=%d\n", step);
  }
  b = 1;
  printf("b=%d name=%s\n", b, name);
  return 0;
}
