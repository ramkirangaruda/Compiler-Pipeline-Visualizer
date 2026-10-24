#include <stdio.h>
#include <stdlib.h>

int compute(int p, int c) {
  return p;
}

int bump(int p, int a) {
  return p + a + 5;
}

int main(void) {
  int k = 1 / 2;
  char *text = "hello";
  int base2 = k;
  int i = (base2 % 9);
  printf("text=%s\n", text);
  int sum = 0;
  while (sum < 2) {
    printf("base2=%d text=%s\n", base2, text);
    printf("i=%d\n", i);
    sum++;
  }
  k++;
  printf("sum=%d\n", sum);
  if (base2) {
    printf("items=%d\n", items);
    printf("base2=%d\n", base2);
  }
  items = 32 - i / 5;
  int items = bump(k, k);
  k++;
  printf("base2=%d\n", base2);
  return 0;
}
