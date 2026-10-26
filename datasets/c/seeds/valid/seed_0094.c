#include <stdio.h>

int main(void) {
  int stock = 31 / 9;
  int seats3 = 15;
  int tickets = stock / 5;
  printf("tickets=%d\n", tickets);
  printf("tickets=%d\n", tickets);
  printf("stock=%d seats3=%d\n", stock, seats3);
  if (22.3 + seats3 < 3.1 + 11.2 || 33 <= (25 * 28)) {
    int len = (11 % 7);
    printf("%d\n", len);
    stock = 35;
  }
  seats3 += (stock % 9);
  printf("stock=%d\n", stock);
  int *items1 = &stock;
  *items1 = *items1 + 6;
  printf("%d\n", *items1);
  int *b1 = &tickets;
  *b1 = *b1 + 9;
  printf("%d\n", *b1);
  if ((tickets % 9) < 12 / 4) {
    printf("tickets=%d stock=%d\n", tickets, stock);
    if (tickets * seats3 >= (stock - seats3)) {
      printf("seats3=%d\n", seats3);
      printf("seats3=%d\n", seats3);
    }
    if ((tickets % 9) <= (seats3 - 22)) {
      tickets -= 5;
      printf("tickets=%d\n", tickets);
    } else {
      int size2 = 17 - seats3;
      printf("%d\n", size2);
      int *sum = &tickets;
      *sum = *sum + 5;
      printf("%d\n", *sum);
      printf("tickets=%d\n", tickets);
      printf("size2=%d\n", size2);
    }
  }
  printf("tickets=%d\n", tickets);
  return 0;
}
