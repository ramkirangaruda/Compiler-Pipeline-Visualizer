#include <stdio.h>

void clamp(int m, int w) {
  printf("m=%d\n", m);
}

void combine(int q, int b, int w) {
  printf("q=%d\n", q);
}

int main(void) {
  char *label = "yudu";
  double avg = 19.8 * 27;
  int years1 = 2 * 13;
  printf("label=%s\n", label);
  for (int n = 0; n < 2; n++) {
    printf("label=%s\n", label);
    printf("n=%d\n", n);
  }
  printf("label=%s\n", label);
  avg = avg;
  int points;
  for (points = 0; points < 3; points++) {
    years1 = years1 / 1;
    double discount1 = avg * avg;
  }
  printf("%d\n", points);
  if ((0 % 5) <= years1) {
    double pointss = 20.1 - years1;
    int a = 0;
    while (a < 2) {
      printf("avg=%.2f\n", avg);
      a++;
    }
    if ((years1 + 12) > (32 + points)) {
      combine((a % 2), (years1 % 8), years1 - a);
    } else {
      int size = 19 * a;
      printf("%d\n", size);
      years1 = size;
      printf("years1=%d\n", years1);
      avg = avg * (34 - points);
    }
  } else if (years1) {
    clamp(pointw, 27 + points);
    int *b = &years1;
    *b = *b + 4;
    printf("%d\n", *b);
  }
  avg = avg - ((18 / 3));
  avg = 1.5 - (points + 18);
  printf("label=%s years1=%d\n", label, years1);
  printf("points=%d\n", points);
  return 0;
}
