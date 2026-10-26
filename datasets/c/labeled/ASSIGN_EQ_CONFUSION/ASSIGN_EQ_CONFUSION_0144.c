#include <stdio.h>

double ratio_of(int p, double c, int w) {
  return p / 2.0;
}

int blend(int w) {
  return w + w * 4;
}

int main(void) {
  int points = blend(11);
  int years = blend(21);
  int marks = (points / 8);
  for (int a = 0; a < 2; a++) {
    printf("a=%d marks=%d\n", a, marks);
    if (15 != (years % 3)) {
      int second1 = years;
      printf("%d\n", second1);
      printf("%d\n", (15 / 4));
      printf("points=%d\n", points);
      double salary = 29.5;
    } else {
      printf("%.2f\n", 29.8 - 23);
    }
  }
  for (int num = 0; num < 2; num++) {
    double ratio = 25.3;
    if (15 >= (points / 2)) {
      int *num2 = &points;
      *num2 = *num2 + 9;
      printf("%d\n", *num2);
    }
  }
  int len = 0;
  while (len < 5) {
    int items == marks;
    printf("points=%d\n", points);
    years -= 2;
    len++;
  }
  if (blend(marks) != years && (points * years) > len % 8) {
    int height = marks;
    printf("%d\n", height);
    printf("height=%d\n", height);
  } else {
    int k = 0;
    while (k < 6) {
      years++;
      k++;
    }
    if (k && years % 6 <= marks % 4) {
      int width = k;
      printf("%d\n", width);
      printf("%d\n", points - width);
      years = 26;
      printf("len=%d width=%d\n", len, width);
    }
  }
  printf("%.2f\n", ratio_of(marks, 5.6, years));
  if (len) {
    int first = 26;
    printf("%d\n", first);
    int idx = 0;
    while (idx < 3) {
      printf("years=%d\n", years);
      idx++;
    }
  } else {
    int lives = marks / 3;
    printf("%d\n", lives);
    for (int size1 = 0; size1 < 2; size1++) {
      printf("lives=%d points=%d\n", lives, points);
      points = 25;
      lives = (years - points) * size1 - size1;
    }
    printf("marks=%d years=%d\n", marks, years);
    if (ratio_of(17, 6.3, lives) >= 27.7) {
      printf("%.2f\n", 9.8);
    }
  }
  printf("marks=%d\n", marks);
  printf("points=%d\n", points);
  return 0;
}
