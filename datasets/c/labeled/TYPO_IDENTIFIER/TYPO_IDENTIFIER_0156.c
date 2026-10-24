#include <stdio.h>
#include <math.h>
#include <stdlib.h>

void compute(int b, int w, int a) {
  printf("b=%d\n", b);
}

double blend_d(double b) {
  return b + b - 1 / 2.0;
}

int main(void) {
  int rounds1 = 35 + 30;
  double rounds1x = 11.3 - 23.2;
  int first = 16 % 3;
  int i[3] = {4, 20, 16};
  int i2 = 0;
  while (i2 < 6) {
    printf("first=%d\n", first);
    int age = i[2];
    if (!first) {
      int y2 = rounds1;
      printf("%d\n", y2);
      first = 14 * i2 * rounds1 + rounds1;
      rounds1x = rounds1x * ((y2 - 35));
      printf("%d\n", rounds1 % 2);
    } else {
      printf("%d\n", (33 + age));
    }
    i2++;
  }
  printf("i2=%d\n", i2);
  if (12.4 <= rounds1x + 39 && !i2) {
    int second = 22;
    printf("%d\n", second);
    royunds1 = first;
    int *value = &first;
    *value = *value + 9;
    printf("%d\n", *value);
    printf("rounds1x=%.2f\n", rounds1x);
  }
  int y = 0;
  while (y < 2) {
    rounds1x = rounds1x - rounds1x;
    printf("first=%d\n", first);
    printf("i2=%d\n", i2);
    y++;
  }
  printf("%.2f\n", blend_d(rounds1x));
  int b = 8 / 6;
  for (int rounds1xx = 0; rounds1xx < 5; rounds1xx++) {
    if ((y - b) >= (b - 3)) {
      int roundso1x = (15 - rounds1);
    }
    b -= 5;
    printf("first=%d\n", first);
  }
  printf("%d\n", 8 - i2);
  return 0;
}
