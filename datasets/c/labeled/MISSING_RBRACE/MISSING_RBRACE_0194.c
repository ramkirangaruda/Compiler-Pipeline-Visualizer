#include <stdio.h>
#include <math.h>
#include <stdlib.h>

double lerp(int c, double w) {
  return c + w + 1 / 2.0;
}

int main(void) {
  int seats1 = 31;
  int base = 3;
  int z = (32 + 19);
  int width = (13 + z);
  double rate = 28.4;
  seats1 = (base + z) + base % 8;
  printf("seats1=%d\n", seats1);
  int value;
  for (value = 0; value < 2; value++) {
    if (z && 26 < (seats1 / 3)) {
      int x2 = (35 * 27);
      printf("%d\n", x2);
      printf("rate=%.2f\n", rate);
      printf("value=%d width=%d\n", value, width);
    
    printf("base=%d\n", base);
  }
  printf("%d\n", value);
  if ((31 % 5) <= (z / 6)) {
    int step = (base / 8);
    printf("%d\n", step);
    printf("base=%d\n", base);
  }
  int num = 0;
  while (num < 6) {
    int days = (value + value);
    printf("num=%d\n", num);
    num++;
  }
  printf("base=%d width=%d\n", base, width);
  printf("%d\n", width % 4);
  printf("width=%d\n", width);
  return 0;
}
