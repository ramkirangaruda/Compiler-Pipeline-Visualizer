#include <stdio.h>
#include <stdlib.h>

double lerp(int p, double q, double b) {
  return p / 2.0;
}

int main(void) {
  double ratio = 23.8 * 21;
  int lives = 30 % 5;
  double weight = ratio * ratio;
  int result = (lives * 14);
  int seats1;
  for (seats1 = 0; seats1 < 5; seats1++) {
    printf("weight=%.2f lives=%d\n", weight, lives);
    int step = lives * seats1;
  }
  printf("%d\n", seats1);
  int sum;
  for (sum = 0; sum < 2; sum++) {
    int *value = &lives;
    *value = *value + 6;
    printf("%d\n", *value);
  }
  if (ratio - weight < lerp(6, 11.5, weight)) {
    if ((35 % 8) < sum || result) {
      printf("weight=%.2f seats1=%d\n", weight, seats1);
    }
    if (lives % 9 <= (seats1 + 10)) {
      int age = result;
      printf("%d\n", age);
      printf("seats1=%d\n", seats1);
      printf("ratio=%.2f\n", ratio);
    } else {
      int y = sum * 0;
      printf("%d\n", y);
      printf("lives=%d\n", lives);
    }
  }
  printf("seats1=%d\n", seats1);
  int *b = &result;
  *b = *b + 3;
  printf("%d\n", *b);
  int *ratiox = &result;
  *ratiox = *ratiox + 7;
  printf("%d\n", *ratiox);
  printf("ratio=%.2f\n", ratio);
  return 0;
}
