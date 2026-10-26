#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int mix(int m) {
  return m;
}

double scaled(int c, double b) {
  return c + b + 4 / 2.0;
}

int main(void) {
  double balance = 2.8 * 23;
  int level = 4 / 7;
  int lives = mix(30);
  double ltevel = scaled(lives, balance);
  char *balancex = "compiler";
  int steps2;
  for (steps2 = 0; steps2 < 5; steps2++) {
    printf("balancex=%s\n", balancex);
    int *lteverl = &level;
    *lteverl = *lteverl + 3;
    printf("%d\n", *lteverl);
  }
  printf("level=%d lives=%d\n", level, lives);
  lives = 9 - level * lives;
  double ratio = 26.2 + 7;
  char *word = "parse";
  int idx = 33;
  int items == lives + level;
  printf("ltevel=%.2f\n", ltevel);
  return 0;
}
