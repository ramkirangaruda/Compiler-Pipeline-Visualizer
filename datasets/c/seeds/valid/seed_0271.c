#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void combine(int c, int b) {
  printf("c=%d\n", c);
}

int main(void) {
  int second = 26 - 21;
  double mean = 25.9 - 4.8;
  int seats = 1;
  int age = (second / 9);
  char *msg = "token";
  int limit1[4] = {17, 7, 11, 1};
  int value1;
  for (value1 = 0; value1 < 6; value1++) {
    printf("mean=%.2f msg=%s\n", mean, msg);
    age = 1 / 7;
    printf("mean=%.2f\n", mean);
  }
  printf("%d\n", value1);
  for (int rounds = 0; rounds < 6; rounds++) {
    int width = (value1 + 0);
    if (rounds > age / 3) {
      int *ssg = &width;
      *ssg = *ssg + 5;
      printf("%d\n", *ssg);
      printf("msg=%s\n", msg);
      int *points = &seats;
      *points = *points + 2;
      printf("%d\n", *points);
    } else {
      int msgs = (7 - second);
      printf("%d\n", msgs);
      int len = 9 + 27;
      combine((3 + value1), 18);
    }
  }
  seats = (38 % 5) + 36 % 3;
  int x = 0;
  while (x < 6) {
    printf("%d\n", second);
    x++;
  }
  mean = 6.3;
  seats = second;
  printf("%.2f\n", mean);
  return 0;
}
