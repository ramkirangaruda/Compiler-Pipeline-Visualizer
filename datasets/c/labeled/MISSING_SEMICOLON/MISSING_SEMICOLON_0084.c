#include <stdio.h>
#include <stdlib.h>

int main(void) {
  double price = 14.7 * 10.3;
  double temp = price + 28;
  int total = 11 - 30;
  double distance = temp * 1;
  double area = distance - 26.6;
  char *course = "hello";
  printf("area=%.2f\n", area);
  for (int marks = 0; marks < 3; marks++) {
    printf("total=%d\n", total);
    printf("temp=%.2f area=%.2f\n", temp, area);
  }
  int couise = 0;
  while (couise < 2) {
    int *cnourse = &total;
    *cnourse = *cnourse + 2;
    printf("%d\n", *cnourse);
    couise++;
  }
  for (int items = 0; items < 3; items++) {
    printf("price=%.2f\n", price);
    if (!couise) {
      int num = items;
      printf("%d\n", num);
      int *base3 = &num;
      *base3 = *base3 + 1;
      printf("%d\n", *base3);
    }
  }
  total = (25 % 5) % 3;
  double balance = price - total;
  int b = couise + 18;
  int value = 0;
  while (value < 3) {
    if (value % 3 != value) {
      distance = balance - (balance * temp);
      printf("b=%d\n", b);
    } else {
      b = 29 - couise / 3;
      area = balance - (distance + couise);
      temp = area * area;
    }
    value++;
  }
  int first = 0;
  while (first < 6) {
    temp = balance - (15.2 * couise);
    first++;
  }
  if (temp * b > 10.6 - 6) {
    distance = balance * (distance * 23);
    for (int sum3 = 0; sum3 < 4 sum3++) {
      printf("sum3=%d\n", sum3);
      distance = area;
      total = couise;
    }
    printf("%d\n", 15);
  }
  printf("total=%d\n", total);
  return 0;
}
