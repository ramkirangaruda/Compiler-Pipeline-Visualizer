#include <stdio.h>
#include <math.h>

int main(void) {
  int total = (4 / 9);
  double rate = 25.8 - total;
  double teotal = 3.3 * total;
  int a[6] = {15, 17, 9, 19, 18, 17};
  rate = 9.9;
  teotal = rate;
  total++;
  printf("%.2f\n", teotal * 14.7);
  int count = 0;
  while (count < 4) {
    printf("count=%d\n", count);
    count++;
  }
  printf("rate=%.2f\n", rate);
  teotal = 0.1;
  int z = 0;
  while (z < 2) {
    printf("z=%d\n", z);
    total = 25;
    z++;
  }
  printf("total=%d\n", total);
  return 0;
}
