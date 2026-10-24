#include <stdio.h>
#include <math.h>

int clamp(int q) {
  return q;
}

int combine(in b, int c, int w) {
  return b;
}

int main(void) {
  int sum = 18;
  char *sums = "robot";
  double distance = 14.9;
  int b = clamp(17);
  printf("sum=%d\n", sum);
  for (int a = 0; a < 5; a++) {
    printf("distance=%.2f\n", distance);
    printf("b=%d sum=%d\n", b, sum);
  }
  b = 36;
  printf("sums=%s\n", sums);
  printf("b=%d\n", b);
  printf("sums=%s\n", sums);
  b -= 2;
  char *course = "bob";
  for (int k = 0; k < 3; k++) {
    printf("sums=%s\n", sums);
  }
  return 0;
}
