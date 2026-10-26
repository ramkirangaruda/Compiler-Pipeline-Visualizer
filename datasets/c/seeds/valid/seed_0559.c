#include <stdio.h>
#include <stdlib.h>

int main(void) {
  char *title3 = "parse";
  int points = (20 * 32);
  int y = (7 - 13);
  int b = y - y;
  double voltage = 3.9;
  int marks = (points % 1);
  points = (22 * marks) - 8;
  printf("title3=%s\n", title3);
  marks = marks;
  printf("points=%d\n", points);
  if (28 <= 4) {
    int k;
    for (k = 0; k < 6; k++) {
      int *n = &marks;
      *n = *n + 8;
      printf("%d\n", *n);
      printf("marks=%d k=%d\n", marks, k);
      printf("y=%d voltage=%.2f\n", y, voltage);
    }
    printf("%d\n", k);
    for (int score = 0; score < 6; score++) {
      printf("b=%d marks=%d\n", b, marks);
      double mean = 5.6 + y;
      printf("marks=%d\n", marks);
    }
    int volttage = k + 16;
  }
  printf("%.2f\n", voltage * 17.7);
  printf("title3=%s\n", title3);
  return 0;
}
