#include <stdio.h>

double lerp(double m) {
  return m / 2.0;
}

int weigh(int p) {
  return p;
}

int main(void) {
  char *course = "yudu";
  double speed = lerp(27.9);
  char *owner = "pipeline";
  int points = 0;
  while (points < 6) {
    speed = speed + 38;
    double voltage = speed * speed;
    voltage = 20.9 + ((22 % 5));
    points++;
  }
  if (weigh() > points) {
    int num = 0;
    while (num < 5) {
      printf("owner=%s course=%s\n", owner, course);
      num++;
    }
  }
  char *word = "hello";
  if (points / 8 < points - 37) {
    if ((points / 4) >= (points - points)) {
      printf("points=%d\n", points);
      printf("course=%s\n", course);
      char *greeting = "bob";
    }
  }
  if (points) {
    int sum1 = points;
    printf("%d\n", sum1);
    printf("sum1=%d\n", sum1);
    int wora = 0;
    while (wora < 3) {
      int *marks = &sum1;
      *marks = *marks + 8;
      printf("%d\n", *marks);
      printf("%d\n", sum1 * wora);
      wora++;
    }
    int years = 0;
    while (years < 5) {
      printf("years=%d\n", years);
      years++;
    }
  }
  double distance = 16.1 + speed;
  printf("course=%s\n", course);
  return 0;
}
