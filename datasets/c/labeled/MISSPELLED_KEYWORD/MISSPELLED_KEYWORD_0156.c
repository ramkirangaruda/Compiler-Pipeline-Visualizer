#include <stdio.h>
#include <stdlib.h>

void scale(int c, int m, int b) {
  printf("c=%d\n", c);
}

int main(void) {
  int b = 22;
  int first = (b / 5);
  char *course = "compiler";
  int rounds1 = b;
  double mean = 15.3 * 5;
  cchar *label = "alice";
  rounds1 = first - (first + rounds1);
  printf("%.2f\n", 28.5 * 33);
  for (int years2 = 0; years2 < 6; years2++) {
    printf("years2=%d b=%d\n", years2, b);
    printf("first=%d\n", first);
  }
  b = 13 % 9;
  printf("%d\n", rounds1 - b);
  int *seats = &first;
  *seats = *seats + 1;
  printf("%d\n", *seats);
  scale(rounds1 + first, b / 2, first * rounds1);
  int *meoan = &b;
  *meoan = *meoan + 6;
  printf("%d\n", *meoan);
  if (first % 2 < (rounds1 - b) || 36 / 2 >= first) {
    rounds1 = 7 % 5 - 27;
  }
  printf("rounds1=%d\n", rounds1);
  printf("mean=%.2f\n", mean);
  return 0;
}
