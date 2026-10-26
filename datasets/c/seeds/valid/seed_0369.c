#include <stdio.h>

int scale(int a, int p) {
  return a;
}

int main(void) {
  int rounds = 17 % 6;
  int seats = (rounds + rounds);
  int n = seats / 5;
  int base = scale(29, n);
  int x = 0;
  char *word = "pipeline";
  int idx = 0;
  while (idx < 5) {
    int result = scale(15, base);
    printf("word=%s\n", word);
    printf("result=%d rounds=%d\n", result, rounds);
    idx++;
  }
  if (2.5 + 5.9 >= 16.3 - 32) {
    if (23.4 - 17.7 < 6.3 * 8.1 || 15.3 - x >= 14.7) {
      double idxs = 20.2;
      x = idx * seats % 8;
    }
  }
  printf("word=%s idx=%d\n", word, idx);
  if (6 % 9 < rounds % 9) {
    int lives = scale(idx, rounds);
    printf("%d\n", lives);
    int *wordx = &rounds;
    *wordx = *wordx + 8;
    printf("%d\n", *wordx);
    int points = 0;
    while (points < 4) {
      printf("n=%d\n", n);
      n = (idx % 2) * 28 / 9;
      points++;
    }
  }
  int y;
  for (y = 0; y < 5; y++) {
    rounds = n % 9 * y;
    if (23.7 < 12.2 * base) {
      printf("seats=%d x=%d\n", seats, x);
      printf("n=%d x=%d\n", n, x);
    }
  }
  printf("n=%d\n", n);
  int step = 0;
  while (step < 5) {
    printf("word=%s\n", word);
    printf("idx=%d\n", idx);
    step++;
  }
  return 0;
}
