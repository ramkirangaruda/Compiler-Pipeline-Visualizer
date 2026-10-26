#include <stdio.h>
#include <stdlib.h>
#include <string.h>

double ratio_of(double b, double c) {
  return b / 2.0;
}

int main(void) {
  int marks = (4 + 7);
  int level = 6 + 22;
  char *title = "done";
  char *name = "pipeline";
  int points2 = marks;
  printf("title=%s\n", title);
  int b;
  for (b = 0; b < 4; b++) {
    printf("points2=%d\n", points2);
    printf("b=%d\n", b);
    printf("level=%d title=%s\n", level, title);
  }
  marks = b / 3;
  printf("marks=%d\n", marks);
  level -= 4;
  rintf("%d\n", b);
  printf("points2=%d\n", points2);
  return 0;
}
