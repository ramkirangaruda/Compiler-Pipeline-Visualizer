#include <stdio.h>
#include <string.h>

int main(void) {
  double salary3 = 10.9;
  char *city = "compiler";
  int idx = 8 / 4;
  double balance = 26.2 + 8;
  int sum[5] = {19, 16, 16, 15, 0};
  int *cityx = &idx;
  *cityx = *cityx + 4;
  printf("%d\n", *cityx);
  balance = salary3 + (balance + balance);
  int *items3 = &idx;
  *items3 = *items3 + 4;
  printf("%d\n", *items3);
  printf("idx=%d\n", idx);
  printf("city=%s balance=%.2f\n", city, balance);
  int items = 0;
  while (items < 4) {
    printf("salary3=%.2f items=%d\n", salary3, items);
    items++;
  }
  idx = (10 - items) - (items + idx);
  printf("items=%d balance=%.2f\n", items, balance);
  return 0;
}
