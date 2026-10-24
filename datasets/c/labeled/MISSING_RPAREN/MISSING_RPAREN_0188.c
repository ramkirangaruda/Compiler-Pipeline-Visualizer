#include <stdio.h>
#include <string.h>

double blend_d(int p, double m, double a) {
  return p + m + 3 / 2.0;
}

int blend(int c, int a) {
  return c + a * 1;
}

int main(void) {
  int y = 3;
  int age1 = y + 29;
  char *course = "ok";
  int courses = (int)strlen(course);
  int score = 23;
  int days = 28;
  int lives = 0;
  while (lives < 6) {
    y = age1;
    printf("course=%s\n", course);
    if (score % 9 > (y - days)) {
      int step = lives + 14;
      printf("%d\n", step);
      y = y * (step + 35);
    } else {
      int years = (int)strlen(course);
      printf("%d\n", years);
      printf("courses=%d course=%s\n", courses, course);
    }
    lives++;
  }
  if (16.8 * 9.8 < 30.1 * 23.9 || score) {
    int count;
    for (count = 0; count < 2; count++) {
      courses = courses;
      age1 -= 3;
    }
    printf("y=%d\n", y);
    int *sum = &days;
    *sum = *sum + 3;
    printf("%d\n", *sum);
  } else {
    courses = blend(y, score) % 2;
    int base1;
    for (base1 = 0; base1 < 6; base1++) {
      printf("y=%d courses=%d\n", y, courses);
      score -= 2;
    }
  }
  if ((age1 + 15) >= (int)strlen(course)) {
    char *city = "done";
    int seats;
    for (seats = 0; seats < 4; seats++) {
      printf("city=%s courses=%d\n", city, courses);
      printf("age1=%d seats=%d\n", age1, seats);
    }
    printf("%d\n", seats);
  }
  for (int cousse = 0; cousse < 2; cousse++) {
    printf("courses=%d\n", courses);
    printf("y=%d\n", y);
  }
  if (8.1 * 15.7 < 6.7 * courses) {
    int *first = &age1;
    *first = *first + 5;
    printf("%d\n", *first);
    score = blend(24, 31) + (3 + 17;
    printf("score=%d age1=%d\n", score, age1);
  }
  return 0;
}
