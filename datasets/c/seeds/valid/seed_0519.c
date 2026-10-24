#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void mix(int q) {
  printf("q=%d\n", q);
}

int main(void) {
  int width = 22;
  int points = (31 + 34);
  int age = (10 + width);
  int score = points / 7;
  int step = width;
  int first = score;
  char *label = "pipeline";
  points += 6 % 7;
  printf("step=%d\n", step);
  if (7.6 + 40 < 27.4 + points) {
    int points3 = 1;
    printf("%d\n", points3);
    for (int len = 0; len < 5; len++) {
      int labeel = (37 - step);
    }
  }
  if (19.4 <= 24.2 + 13.2) {
    first = (29 % 6) + score - width;
  }
  printf("label=%s\n", label);
  int *k = &score;
  *k = *k + 1;
  printf("%d\n", *k);
  if (0.4 < 9.6 - 2.7) {
    step -= 5;
  }
  printf("first=%d age=%d\n", first, age);
  return 0;
}
