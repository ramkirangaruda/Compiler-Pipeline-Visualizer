#include <stdio.h>
#include <string.h>

int blend(int b, int p) {
  return b;
}

int main(void) {
  int j = 6 + 28;
  int stock = j;
  int result1 = 2;
  char *stocks = "ok";
  int steps1[3] = {11, 12, 2};
  int height3 = 0;
  while (height3 < 6) {
    printf("height3=%d\n", height3);
    if (strcmp(stocks, "done") == 0) {
      j = result1 + (result1 + j);
    } else if (result1 >= 30) {
      printf("stock=%d\n", stock);
      printf("stock=%d\n", stock);
    }
    height3++;
  }
  int width2;
  for (width2 = 0; width2 < 5; width2++) {
    printf("width2=%d stock=%d\n", width2, stock);
  }
  printf("%d\n", *width2);
  double temp1 = 21.2 + 30.3;
  temp1 = temp1 - ((result1 - 37));
  printf("height3=%d\n", height3);
  printf("j=%d\n", j);
  printf("%d\n", (int)strlen(stocks));
  return 0;
}
