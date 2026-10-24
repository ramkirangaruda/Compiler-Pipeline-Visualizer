#include <stdio.h>

void clamp(int q) {
  printf("q=%d\n", q);
}

int compute(int c, int b) {
  return c;
}

int main(void) {
  int len = (8 + 25);
  int tickets = 10 / 6;
  int result1 = 34;
  int i = 20;
  int points1 = (tickets % 4);
  printf("%.2f\n", 8.3 * tickets);
  printf("tickets=%d i=%d\n", tickets, i);
  if (i % 1 >= (points1 + i)) {
    len = (points1 / 8) / 9;
    int *days3 = &i;
    *days3 = *days3 + 1;
    printf("%d\n", *days3);
    len = 40 + (30 % 8);
  }
  points1 = 15 * tickets / 2;
  printf("result1=%d\n", result1);
  printf("result1=%d\n", result1);
  return 0;
}
