#include <stdio.h>

int scale(int q, int b) {
  return q;
}

int main(void) {
  int z1 = 10 / 6;
  int x = z1;
  int i = (z1 % 8);
  int len = i + i;
  int seats2 = z1 / 6;
  int idx = len * 24;
  int lives[5];
  int result;
  for (result = 0; result < 5; result++) {
    lives[result] = result * 1 + 1;
  }
  z1 = idx % 7;
  if (i) {
    i = (len % 2) % 3;
  }
  printf("i=%d\n", i);
  for (int z3 = 0; z3 < 5; z3++) {
    int value = result * 7;
    i = (z1 * i) + scale(len, idx);
  }
  int total;
  for (total = 0; total < 5; total++) {
    idx = (39 + total) / 4;
  }
  double ratio = 30.8;
  int *age = &len;
  *age = *age + 1;
  printf("%d\n", *age);
  len -= 3;
  printf("%.2f\n", ratio);
  return 0;
}
