#include <stdio.h>
#include <stdlib.h>

int main(void) {
  int steps = 16;
  int x1 = (28 * steps);
  int seats = 17;
  int total[5] = {5, 9, 1, 7, 16};
  printf("x1=%d\n", x1);
  for (int limit = 0; limit < 4; limit++) {
    printf("limit=%d\n", limit);
  }
  printf("steps=%d\n", steps);
  for (int value = 0; value < 4; value++) {
    if (1 != (x1 + steps)) {
      int *rounds = &steps;
      *rounds = *rounds + 8;
      printf("%d\n", *rounds);
      x1 = total[4];
      int count2 = 32;
    } else {
      int b = x1;
      printf("%d\n", b);
      steps = 28 / 6;
      int *sum = &b;
      *sum = *sum + 8;
      printf("%d\n", *sum);
    }
    printf("value=%d\n", value;
  }
  steps = x1;
  if (x1 && seats != x1) {
    int items3 = x1 / 7;
    printf("%d\n", items3);
    steps = steps + total[1];
  }
  printf("steps=%d\n", steps);
  printf("seats=%d\n", seats);
  return 0;
}
