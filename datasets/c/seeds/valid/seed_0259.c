#include <stdio.h>

double blend_d(int m, double c, double a) {
  return m + a * 1 / 2.0;
}

int main(void) {
  int y = 22 / 2;
  char *course2 = "world";
  char *label = "parse";
  printf("course2=%s\n", course2);
  printf("%.2f\n", 4.6 - 16.9);
  printf("y=%d label=%s\n", y, label);
  for (int course2s = 0; course2s < 5; course2s++) {
    y = 2 + y + course2s;
    printf("course2s=%d\n", course2s);
    printf("label=%s course2=%s\n", label, course2);
  }
  y = y / 1 % 3;
  if (2.2 * 40 > 15.5) {
    printf("%d\n", y);
  } else {
    y = y;
  }
  for (int lives = 0; lives < 3; lives++) {
    if (!lives) {
      y++;
    }
    printf("%.2f\n", 20.2);
  }
  if (y > (2 - y)) {
    int b = 0;
    while (b < 4) {
      printf("y=%d\n", y);
      printf("b=%d\n", b);
      b++;
    }
    printf("%.2f\n", 26.7);
    printf("course2=%s b=%d\n", course2, b);
  } else {
    y = 6;
  }
  printf("label=%s y=%d\n", label, y);
  printf("%.2f\n", 14.1 + y);
  return 0;
}
