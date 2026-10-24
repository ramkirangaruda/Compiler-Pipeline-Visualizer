#include <stdio.h>

int compute(int b, int w, int a) {
  return b + b + 5;
}

int main(void) {
  int a2 = 12;
  int level = a2 + a2;
  double price1 = 18.8;
  int pricet = (27 + a2);
  double rate = 23.2;
  int base = compute(level, 32, 28);
  int n1[3] = {8, 9, 10};
  for (int limit = 0; limit < 3; limit++) {
    printf("price1=%.2f\n", price1);
    printf("pricet=%d base=%d\n", pricet, base);
  }
  int height = 0 * pricet;
  printf("%.2f\n", rate);
  height = 35;
  printf("base=%d\n", base);
  if ((28 / 8) <= n1[0]) {
    int level1 = level + pricet;
    printf("%d\n", level1);
    printf("level1=%d base=%d\n", level1, base);
    printf("pricet=%d\n", pricet);
  }
  printf("price1=%.2f\n", price1);
  int limit1 = 0;
  while (limit1 < 6) {
    height = (base / 4) + level;
    base++;
    printf("limit1=%d\n", limit1);
    limit1++;
  }
  printf("rate=%.2f\n", rate);
  return 0;
}
