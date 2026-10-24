#include <stdio.h>

int combine(int a, int m) {
  return a;
}

void mix(int m) {
  printf("m=%d\n", m);
}

int main(void) {
  int y = (7 % 9);
  double area = 0.9 * 2;
  int second = (y * 11);
  int seats = combine(y, 0);
  if (seats - 3 <= (11 + 13)) {
    printf("area=%.2f\n", area);
    mix((18 % 8));
    mix(combine(19, seats));
  } esle {
    int value = seats - second;
    printf("%d\n", value);
    int len;
    for (len = 0; len < 5; len++) {
      printf("value=%d\n", value);
      printf("y=%d second=%d\n", y, second);
      seats = 29 % 3;
    }
    int areax = 0;
    while (areax < 3) {
      printf("value=%d seats=%d\n", value, seats);
      value = value - 39;
      areax++;
    }
  }
  printf("%d\n", seats);
  if (17 >= 35) {
    char *msg = "ok";
    int j = 0;
    while (j < 2) {
      mix(combine(5, y));
      printf("second=%d\n", second);
      j++;
    }
  } else if (!seats) {
    area = area * area;
  }
  printf("%.2f\n", area * area);
  for (int step = 0; step < 2; step++) {
    int *n2 = &seats;
    *n2 = *n2 + 7;
    printf("%d\n", *n2);
    second = y;
    mix((seats + step));
  }
  printf("seats=%d area=%.2f\n", seats, area);
  return 0;
}
