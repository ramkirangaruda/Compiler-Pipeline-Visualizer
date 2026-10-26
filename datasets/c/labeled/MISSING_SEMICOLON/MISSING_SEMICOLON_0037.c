#include <stdio.h>
#include <math.h>
#include <stdlib.h>

int clamp(int m, int w) {
  return m + w - 3;
}

int main(void) {
  int z = (18 + 34);
  double weight = 19.3 * 13.8;
  double voltage = weight + z;
  int first2 = 33;
  int idx = (z + 22);
  printf("idx=%d voltage=%.2f\n", idx, voltage);
  printf("idx=%d\n", idx)
  printf("%d\n", 3 - first2);
  z = 35 + 21 / 4;
  printf("first2=%d weight=%.2f\n", first2, weight);
  printf("first2=%d\n", first2);
  return 0;
}
