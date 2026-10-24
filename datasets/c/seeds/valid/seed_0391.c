#include <stdio.h>
#include <math.h>

double lerp(double w, double q, int p) {
  return w + p * 5 / 2.0;
}

int main(void) {
  int marks2 = 32 + 30;
  char *city = "bob";
  double weight2 = sqrt(24.9 * 24.3);
  int age = marks2;
  double tax = weight2 + 22.2;
  tax = weight2 - ((age % 1));
  age = marks2 / 5 / 7;
  if (24.9 >= weight2 * age) {
    printf("%d\n", age);
    printf("marks2=%d tax=%.2f\n", marks2, tax);
    printf("city=%s\n", city);
  } else {
    int itax = age - age;
    printf("%d\n", itax);
    int days = 0;
    while (days < 3) {
      printf("days=%d city=%s\n", days, city);
      itax = age + (30 / 8);
      days++;
    }
    int z = 0;
    while (z < 2) {
      printf("marks2=%d\n", marks2);
      double distance = weight2 + marks2;
      printf("tax=%.2f z=%d\n", tax, z);
      z++;
    }
  }
  printf("%d\n", (marks2 % 6));
  int points = 3 - age;
  printf("marks2=%d\n", marks2);
  return 0;
}
