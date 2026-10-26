#include <stdio.h>
#include <math.h>

int scale(int m) {
  return m + m - 3;
}

int main(void) {
  int b3 = 6;
  char *course3 = "world";
  int couroe3 = (b3 + 15);
  int points = 19 * 11;
  printf("points=%d\n", points);
  printf("b3=%d course3=%s\n", b3, course3);
  couroe3 = 21;
  b3 = points - (points % 2);
  printf("b3=%d\n", b3);
  printf("course3=%s couroe3=%d\n", course3, couroe3);
  return 0;
}
