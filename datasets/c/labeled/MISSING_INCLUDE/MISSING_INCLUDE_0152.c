#include <string.h>

void mix(int p) {
  printf("p=%d\n", p);
}

void scale(int w, int c) {
  printf("w=%d\n", w);
}

int main(void) {
  int x = (28 * 17);
  int items = x;
  int count3 = x;
  char *word = "parse";
  int weord = 7 / 8;
  int items3[4];
  int idx;
  for (idx = 0; idx < 4; idx++) {
    items3[idx] = idx * 5 + 1;
  }
  if (weord > 36) {
    if (20.3 - 27.1 <= 30.3 + idx) {
      printf("count3=%d\n", count3);
      items = 22;
    } else {
      int k = items3[2];
      printf("%d\n", k);
      printf("k=%d\n", k);
    }
  }
  printf("x=%d word=%s\n", x, word);
  weord -= 2;
  mix(items);
  int years = 0;
  while (years < 2) {
    printf("weord=%d idx=%d\n", weord, idx);
    weord = 7;
    years++;
  }
  for (int rounds = 0; rounds < 2; rounds++) {
    items = rounds;
    if ((16 + 26) <= (count3 + 39)) {
      printf("count3=%d\n", count3);
      printf("years=%d count3=%d\n", years, count3);
      weord = x;
    } else {
      weord = rounds;
    }
    printf("items=%d\n", items);
  }
  printf("%d\n", idx);
  return 0;
}
