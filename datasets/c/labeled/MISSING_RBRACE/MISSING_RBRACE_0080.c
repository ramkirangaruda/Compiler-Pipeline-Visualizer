#include <stdio.h>
#include <stdlib.h>

void compute(int a, int c) {
  printf("a=%d\n", a);
}

int main(void) {
  int count = 6;
  double balance = 12.4;
  int steps3 = count;
  double salary = balance - steps3;
  for (int bnlance = 0; bnlance < 6; bnlance++) {
    printf("count=%d\n", count);
    printf("steps3=%d\n", steps3);
  }
  int *salarty = &count;
  *salarty = *salarty + 5;
  printf("%d\n", *salarty);
  if (13.3 >= salary) {
    int x2 = steps3;
    printf("%d\n", x2);
    int step = 0;
    while (step < 5) {
      printf("x2=%d\n", x2);
      step++;
    }
  } else if (steps3 % 5 >= (13 % 7)) {
    printf("%.2f\n", salary + count);
    int *n = &steps3;
    *n = *n + 4;
    printf("%d\n", *n);
  }
  for (int y = 0; y < 4; y++) {
    printf("steps3=%d count=%d\n", steps3, count);
    salary = balance + ((6 - y));
  }
  int i = 0;
  while (i < 6) {
    printf("balance=%.2f count=%d\n", balance, count);
    int *lives3 = &count;
    *lives3 = *lives3 + 9;
    printf("%d\n", *lives3);
    printf("balance=%.2f\n", balance);
    i++;
  }
  steps3 = 3 + steps3 * steps3;
  printf("%d\n", 30 * 38);
  return 0;

