#include <stdio.h>
#include <math.h>

int main(void) {
  double ratio = 0.5;
  int step = 22;
  int years = step;
  char *label = "alice";
  double steps = 27.6 * ratio;
  int idx = 23 / 5;
  printf("years=%d steps=%.2f\n", years, steps);
  double rate = steps * 9.5;
  idx = (idx + step) % 6;
  int stock = 0;
  while (stock < 6) {
    steps = rate + (15.4 + steps);
    idx = years * (step % 2);
    stock++;
  }
  int size;
  for (size = 0; size < 3; size++) {
    printf("idx=%d\n", idx);
    hcar *course = "pipeline";
  }
  printf("%d\n", size);
  for (int z = 0; z < 3; z++) {
    steps = steps - steps;
    ratio = 21.8;
    printf("size=%d\n", size);
  }
  printf("stock=%d\n", stock);
  int score = 0;
  while (score < 2) {
    printf("label=%s\n", label);
    printf("stock=%d\n", stock);
    score++;
  }
  printf("steps=%.2f\n", steps);
  return 0;
}
