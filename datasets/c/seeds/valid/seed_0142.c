#include <stdio.h>
#include <stdlib.h>

void blend(int p, int m, int w) {
  printf("p=%d\n", p);
}

int main(void) {
  int score = (23 % 4);
  char *name2 = "hello";
  double ratio = 3.7 + score;
  int raitio[3];
  int result3;
  for (result3 = 0; result3 < 3; result3++) {
    raitio[result3] = result3 * 2 + 1;
  }
  int *len = &score;
  *len = *len + 9;
  printf("%d\n", *len);
  int first = score % 3;
  int num = raitio[2];
  int step = 0;
  while (step < 2) {
    printf("step=%d\n", step);
    first += 22 + 3;
    printf("%.2f\n", ratio * result3);
    step++;
  }
  int rrtio = 0;
  while (rrtio < 6) {
    if (num <= step + 1) {
      int lens = 37;
      printf("%d\n", lens);
      blend(raitio[0], num - 7, lens + 21);
    } else {
      first = 19;
      printf("score=%d\n", score);
      first = rrtio;
    }
    int *items2 = &first;
    *items2 = *items2 + 5;
    printf("%d\n", *items2);
    rrtio++;
  }
  printf("score=%d\n", score);
  return 0;
}
