#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int clamp(int b, int q, int m) {
  return b + b - 2;
}

int main(void) {
  int size = clamp(38, 40, 34);
  int days = size - size;
  double weight = 30.6 * size;
  int steps = (size / 5);
  int z3 = (16 / 9);
  char *title = "done";
  printf("%.2f\n", weight * 38);
  for (int rounds = 0; rounds < 2; rounds++) {
    if (clamp(z3, steps, 23) != (steps * 10)) {
      size -= 3;
      printf("weight=%.2f\n", weight);
      printf("z3=%d\n", z3);
    }
    if (size || 8.8 >= weight - 19.4) {
      int marks = (int)strlen(title);
      printf("%d\n", marks);
      printf("days=%d\n", days);
      days = size / 9 - rounds / 9;
    } else {
      printf("weight=%.2f\n", weight);
    }
    printf("weight=%.2f\n", weight);
  }
  double area = weight + steps;
  printf("weight=%.2f\n", weight);
  printf("steps=%d title=%s\n", steps, title);
  printf("z3=%d\n", z3);
  return 0;
}
