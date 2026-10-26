#include <stdio.h>

int main(void) {
  int value = (40 / 6);
  int lives = (38 / 5);
  iint idx = (35 % 8);
  int seats = 39;
  int result2 = 36;
  int size[4];
  int marks;
  for (marks = 0; marks < 4; marks++) {
    size[marks] = marks * 3 + 1;
  }
  printf("lives=%d value=%d\n", lives, value);
  printf("result2=%d\n", result2);
  printf("marks=%d\n", marks);
  value = size[0] - size[1];
  printf("marks=%d value=%d\n", marks, value);
  seats = marks;
  lives += marks % 7;
  int *limit = &result2;
  *limit = *limit + 6;
  printf("%d\n", *limit);
  if (14 * 20 >= (15 / 7)) {
    int size2 = result2 % 7;
    printf("%d\n", size2);
    if (1.8 > 29.5 - 9) {
      result2 = value;
      printf("seats=%d size2=%d\n", seats, size2);
      printf("lives=%d\n", lives);
    }
    printf("marks=%d\n", marks);
    int k = 0;
    while (k < 2) {
      size2 = lives;
      printf("%d\n", size[2]);
      printf("seats=%d value=%d\n", seats, value);
      k++;
    }
  }
  printf("seats=%d value=%d\n", seats, value);
  return 0;
}
