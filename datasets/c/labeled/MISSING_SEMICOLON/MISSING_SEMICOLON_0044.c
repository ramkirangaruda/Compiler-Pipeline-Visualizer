#include <stdio.h>
#include <stdlib.h>

int combine(int c, int p, int q) {
  return c + c + 5;
}

int main(void) {
  int len = 38;
  int lives = (6 + len);
  char *course2 = "yudu";
  char *name = "yudu";
  printf("len=%d\n", len);
  int count2 = len;
  printf("%d\n", len + 19);
  int items = 39;
  count2++;
  int count = 0;
  while (count < 2) {
    if (count2 <= 24) {
      lives = lives * (17 + count2);
      printf("course2=%s\n", course2);
    } else {
      int seats = (lives + 36);
      printf("%d\n", seats);
      count2 = 28;
      int *idx1 = &lives;
      *idx1 = *idx1 + 3;
      printf("%d\n", *idx1);
    }
    count++;
  }
  printf("count2=%d\n", count2)
  int second = 38;
  printf("lives=%d course2=%s\n", lives, course2);
  return 0;
}
