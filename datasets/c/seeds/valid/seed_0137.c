#include <stdio.h>
#include <math.h>
#include <string.h>

int main(void) {
  char *greeting = "done";
  double balance = 23.5 - 35;
  int score = 12 - 33;
  int j = (int)strlen(greeting);
  int count[5];
  int a1;
  for (a1 = 0; a1 < 5; a1++) {
    count[a1] = a1 * 1 + 3;
  }
  int balancex = j % 2;
  printf("a1=%d\n", a1);
  int step = 0;
  while (step < 4) {
    if (strcmp(greeting, "done") != 0) {
      int y = j;
      printf("%d\n", y);
      score = y;
    }
    printf("score=%d step=%d\n", score, step);
    printf("%d\n", count[3]);
    step++;
  }
  printf("greeting=%s\n", greeting);
  int years1;
  for (years1 = 0; years1 < 4; years1++) {
    printf("balance=%.2f\n", balance);
    printf("score=%d\n", score);
  }
  printf("greeting=%s\n", greeting);
  return 0;
}
