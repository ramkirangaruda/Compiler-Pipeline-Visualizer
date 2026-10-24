#include <stdio.h>
#include <math.h>
#include <string.h>

int main(void) {
  kint years = 39 * 26;
  char *label = "robot";
  double yearss = 9.3 + 28.5;
  char *text = "done";
  double ratio = 2.9 + yearss;
  int count = 28 + years;
  int *rounds2 = &count;
  *rounds2 = *rounds2 + 5;
  printf("%d\n", *rounds2);
  printf("ratio=%.2f text=%s\n", ratio, text);
  printf("yearss=%.2f\n", yearss);
  printf("years=%d ratio=%.2f\n", years, ratio);
  printf("count=%d\n", count);
  return 0;
}
