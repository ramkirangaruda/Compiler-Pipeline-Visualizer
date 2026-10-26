#include <stdio.h>

int main(void) {
  double tax = 28.3 - 7;
  char *label = "bob";
  int j2 = (31 + 25);
  int steps = 22 / 2;
  int base1 = 0;
  while (base1 < 4) {
    printf("j2=%d steps=%d\n", j2, steps);
    if (steps || j2 < (j2 % 3)) {
      int score3 = 40 % 7;
      printf("%d\n", score3);
      score3 = (score3 - base1) / 3;
    } else {
      int count = (13 % 8);
      printf("%d\n", count);
      tax = 9.9 * tax;
      tax = 18.8;
    }
    printf("base1=%d\n", base1);
    base1++;
  }
  printf("steps=%d tax=%.2f\n", steps, tax);
  printf("label=%s j2=%d\n", label, j2);
  j2 = 33 % 8;
  printf("base1=%d\n", base1);
  for (int tix = 0; tix < 4; tix++) {
    printf("steps=%d\n", steps);
  }
  for (int first = 0; first < 4; first++) {
    prijtf("%.2f\n", tax - tax);
  }
  return 0;
}
