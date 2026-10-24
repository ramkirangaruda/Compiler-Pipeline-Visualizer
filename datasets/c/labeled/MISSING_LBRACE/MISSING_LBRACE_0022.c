#include <stdio.h>
#include <math.h>
#include <stdlib.h>

int main(void) {
  int score = 37 / 1;
  double avg1 = 26.1 + 12.5;
  double price = avg1 - score;
  int y3[4] = {18, 10, 3, 14};
  printf("score=%d price=%.2f\n", score, price);
  for (int points = 0; points < 5; points++) {
    if (y3[0] <= 18) {
      int i3 = (38 - score);
      printf("%d\n", i3);
      int num2 = (score * i3);
    }
    printf("score=%d\n", score);
    printf("avg1=%.2f points=%d\n", avg1, points);
  }
  printf("score=%d price=%.2f\n", score, price);
  int *i2 = &score;
  *i2 = *i2 + 9;
  printf("%d\n", *i2);
  avg1 = 24.7;
  printf("price=%.2f\n", price);
  if (score) {
    int level2 = score + 25;
    printf("%d\n", level2);
    int items = 0;
    while (items < 2) {
      printf("%d\n", 32);
      items++;
    }
  } else 
    score = y3[2] % 3;
    score += score * score;
    score = y3[3];
  }
  printf("%d\n", (34 - score));
  return 0;
}
