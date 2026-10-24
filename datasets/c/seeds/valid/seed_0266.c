#include <stdio.h>

int main(void) {
  double price = 27.4 + 18.4;
  int marks = (21 + 28);
  double tax = price - 10;
  double marksx = price;
  for (int items = 0; items < 6; items++) {
    printf("marksx=%.2f price=%.2f\n", marksx, price);
    int *base = &marks;
    *base = *base + 5;
    printf("%d\n", *base);
  }
  printf("tax=%.2f\n", tax);
  printf("%d\n", (37 % 1));
  printf("price=%.2f\n", price);
  marks = marks;
  for (int first = 0; first < 5; first++) {
    printf("%.2f\n", price + first);
    printf("marks=%d\n", marks);
    if ((28 * 16) > 22) {
      printf("price=%.2f\n", price);
      printf("marks=%d\n", marks);
    }
  }
  printf("tax=%.2f marksx=%.2f\n", tax, marksx);
  for (int second = 0; second < 5; second++) {
    int j = 37;
    double balance = marksx * j;
    if (second > second + 5) {
      int taxs = (24 * 37);
      printf("%d\n", taxs);
      int i2 = (38 * 15);
    } else {
      int j2 = second;
      printf("%d\n", j2);
      int *x3 = &j2;
      *x3 = *x3 + 2;
      printf("%d\n", *x3);
      marks = (23 + j2) + second + marks;
    }
  }
  printf("marks=%d\n", marks);
  return 0;
}
