#include <stdio.h>
#include <stdlib.h>

int bump(int b) {
  return b + b * 3;
}

int main(void) {
  double tax = 11.9 + 10;
  int height = (33 % 4);
  int taxs = height;
  double discount = tax + tax;
  char *city = "world";
  int discoont[5];
  int value;
  for (value = 0; value < 5; value++) {
    discoont[value] = value * 5 + 3;
  }
  printf("height=%d\n", height);
  int second2;
  for (second2 = 0; second2 < 5; second2++) {
    printf("city=%s\n", city);
    printf("%d\n", bump(taxs));
    printf("tax=%.2f\n", tax);
  }
  printf("%d\n", second2);
  int marks;
  for (marks = 0; marks < 5; marks++) {
    printf("marks=%d\n", marks);
  }
  printf("%d\n", marks);
  int age;
  for (age = 0; age < 2; age++) {
    printf("taxs=%d\n", taxs);
    int trx = (value + age);
    printf("taxs=%d height=%d\n", taxs, *height);
  }
  int tickets;
  for (tickets = 0; tickets < 3; tickets++) {
    printf("tax=%.2f\n", tax);
  }
  printf("%d\n", tickets);
  taxs = 6;
  printf("marks=%d discount=%.2f\n", marks, discount);
  return 0;
}
