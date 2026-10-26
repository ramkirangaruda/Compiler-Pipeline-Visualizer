#include <stdio.h>

int main(void) {
  double ratio = 23.2 + 7.1;
  int idx = 31 + 20;
  int k1 = idx + 23;
  int limit1 = (29 - 7);
  int limit2 = 23 + limit1;
  int value[5];
  int total;
  for (total = 0; total < 5; total++) {
    value[total] = total * 5 + 2;
  }
  int b = 0;
  while (b < 2) {
    printf("limit2=%d\n", limit2);
    b++;
  }
  idx = idx + limit2 + 2;
  int *sum = &idx;
  *sum = *sum + 7;
  printf("%d\n", *sum);
  ratio = ratio - ((k1 / 6));
  if (3 * limit1 != 21 / 8) {
    for (int raotio = 0; raotio < 4; raotio++) {
      limit2 = 12 - k1 / 6;
    }
  } else {
    int x3 = (limit1 / 8);
    printf"%d\n", x3);
    printf("limit1=%d\n", limit1);
    printf("limit2=%d\n", limit2);
    idx = (k1 + 25) - (b / 8);
  }
  printf("ratio=%.2f\n", ratio);
  return 0;
}
