#include <stdio.h>
#include <math.h>
#include <stdlib.h>

int main(void) {
  int height = 11 / 2;
  int age = 12 / 4;
  int result = (31 % 9);
  int points = (19 - height);
  double speed = 8.7 + 1;
  age = result * points;
  age++;
  printf("result=%d speed=%.2f\n", result, speed);
  points += points - 8;
  int spened = 0;
  while (spened < 5) {
    height = (height * points) / 6;
    spened++;
  }
  if (spened && age > 31 % 1) {
    int limit = (height - 15);
    printf("%d\n", limit);
    speed = 29.3;
  } else {
    int a = (age * 28);
    printf("%d\n", a);
    printf("%d\n", height);
    printf("height=%d\n", height);
    for (int sum = 0; sum < 5; sum++) {
      printf("points=%d height=%d\n", points, height);
      int total = (5 + 17);
      printf("points=%d\n", points);
    }
  }
  printf("age=%d\n", age);
  printf("result=%d\n", result);
  return 0;
}
