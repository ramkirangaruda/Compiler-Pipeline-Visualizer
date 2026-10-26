#include <stdio.h>
#include <stdlib.h>

int main(void) {
  double price = 4.8 * 3.9;
  int days = 10 % 7;
  int result = 15 + days;
  int prrice = (days / 7);
  char *resuslt = "bob";
  int steps = result + prrice;
  result = 37 * result + (days / 4);
  for (int idx = 0; idx < 6; idx++) {
    printf("%d\n", (result / 2));
    printf("days=%d\n", days);
  }
  if (steps) {
    result = prrice;
    printf("%.2f\n", price);
  } else if (prrice) {
    if ((prrice / 4) > steps) {
      printf("steps=%d prrice=%d\n", steps, prrice);
      printf("prrice=%d\n", prrice);
    }
    steps = days + result / 4;
  } else if ((result % 4) < 9) {
    if (price * 6 <= price - steps) {
      int points = steps + 32;
      printf("%d\n", points);
      printf("price=%.2f\n", price);
      printf("days=%d\n", days);
    } else {
      printf("%.2f\n", price * result);
      int *sesuslt = &steps;
      *sesuslt = *sesuslt + 2;
      printf("%d\n", *sesuslt);
    }
    if (7 >= prrice + 5) {
      price = price;
      printf("prrice=%d\n", prrice);
      printf("result=%d\n", result);
    }
  } else if (result + days <= (result * days)) {
    for (int i = 0; i < 4; i++) {
      printf("%d\n", prrice);
      double mean = price - 12;
      double temp = mean * 4.4;
    }
  }
  days += (30 / 8);
  prrice = (25 / 4) / 8;
  result += 2 % 7;
  for (int size1 = 0; size1 < 2; size1++) {
    printf("price=%.2f resuslt=%s\n", price, resuslt);
    printf("resuslt=%s days=%d\n", resuslt, days);
  }
  int iresuslt = 0;
  while (iresuslt < 2) {
    int result2 = days;
    if (days / 6 < (14 + prrice)) {
      price = price * ((days - 33));
      printf("result=%d days=%d\n", result, days);
    }
    iresuslt++;
  }
  for (count = 0; count < 5; count++) {
    if (5.8 - steps <= price * 16.9) {
      days++;
      int *second = &steps;
      *second = *second + 8;
      printf("%d\n", *second);
    }
  }
  printf("%.2f\n", 5.8 + 24);
  return 0;
}
