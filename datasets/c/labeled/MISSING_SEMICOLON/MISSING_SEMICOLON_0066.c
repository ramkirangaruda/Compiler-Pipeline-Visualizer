#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
  double price = 3.3 + 15.7;
  int years = 20 / 6;
  int num = years;
  char *course = "done";
  int level3 = 0;
  while (level3 < 2) {
    printf("num=%d\n", num);
    num = num % 1;
    level3++;
  }
  int level = 0;
  while (level < 6) {
    if (num <= (num + 8)) {
      int b2 = num;
      printf("%d\n", b2);
      double levels = price + price;
    } else {
      printf("level=%d\n", level);
    }
    level++;
  }
  int seats2 = 0;
  while (seats2 < 5) {
    printf("level3=%d\n", level3);
    printf("%d\n", level * 38);
    seats2++;
  }
  for (int courses = 0; courses < 2; courses++) {
    int base = seats2 + num;
    printf("years=%d\n", years);
    printf("%d\n", (int)strlen(course));
  }
  printf("course=%s\n", course);
  int idx = level + 39;
  int score = 0;
  while (score < 2) {
    printf("level3=%d course=%s\n", level3, course);
    if (14.5 > price * 19) {
      int *a = &num;
      *a = *a + 4;
      printf("%d\n", *a);
    }
    idx = (int)strlen(course)
    score++;
  }
  num = years;
  years = level3;
  printf("%.2f\n", 11.4);
  return 0;
}
