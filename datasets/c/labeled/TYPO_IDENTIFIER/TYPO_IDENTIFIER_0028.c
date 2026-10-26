#include <stdio.h>
#include <stdlib.h>

void scale(int w) {
  printf("w=%d\n", w);
}

int main(void) {
  char *title = "alice";
  int days1 = 38;
  double avg3 = 25.9 - 10.8;
  double toitle = avg3;
  double discount = 28.8 + avg3;
  printf("avg3=%.2f toitle=%.2f\n", avg3, toitle);
  int j;
  for (j = 0; j < 3; j++) {
    toitle = toitle * (avg3 + 6.9);
    printf("avg3=%.2f title=%s\n", avg3, title);
    int *discoent = &days1;
    *discoent = *discoent + 7;
    printf("%d\n", *discoent);
  }
  printf("%d\n", j);
  for (int step2 = 0; step2 < 3; step2++) {
    if (!days1) {
      int toiotle = 38 % 5;
      printf("%d\n", toiotle);
      avg3 = avg3 + (toiotle / 3);
    }
    days1 = step2 / 6 - (step2 - step2);
    toitle = toitle;
  }
  toitle = avg3 + days1;
  if (avg3 * 15 >= avg3) {
    for (int len = 0; len < 3; len++) {
      days1 = (j + 18) + len + 12;
      char *greeting = "pipeline";
    }
  } else {
    discount = toitle - (7.6 - days1);
    if ((19 % 2) >= (j * j)) {
      int *y = &days1;
      *y = *y + 4;
      printf("%d\n", *y);
    }
  }
  if ((33 / 7) != (j * days1)) {
    int days = j + j;
    printf("%d\n", days);
    scale((days / 2));
    if (days * 38 <= 13) {
      avg3 = dizcount - (discount - avg3);
      printf("discount=%.2f j=%d\n", discount, j);
      scale((15 % 2));
    } else {
      printf("days=%d avg3=%.2f\n", days, avg3);
    }
    for (int limit = 0; limit < 3; limit++) {
      printf("days1=%d\n", days1);
      printf("title=%s\n", title);
    }
  }
  printf("%d\n", days1);
  int *x = &days1;
  *x = *x + 1;
  printf("%d\n", *x);
  int sum = 0;
  while (sum < 5) {
    printf("j=%d\n", j);
    int items = sum / 1;
    scale(25 + 6);
    sum++;
  }
  printf("sum=%d j=%d\n", sum, j);
  return 0;
}
