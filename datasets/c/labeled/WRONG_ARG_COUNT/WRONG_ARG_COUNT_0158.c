#include <stdio.h>

int compute(int p) {
  return p;
}

int main(void) {
  int days = 16 + 7;
  int seats1 = compute(27);
  int i = compute(9, 1);
  double distance = 19.7 - 28;
  int years3 = 10;
  char *adistance = "pipeline";
  int years1;
  for (years1 = 0; years1 < 5; years1++) {
    printf("years1=%d distance=%.2f\n", years1, distance);
  }
  printf("%d\n", years1);
  printf("distance=%.2f\n", distance);
  int a;
  for (a = 0; a < 2; a++) {
    printf("a=%d years1=%d\n", a, years1);
    printf("seats1=%d\n", seats1);
    printf("seats1=%d years3=%d\n", seats1, years3);
  }
  printf("%d\n", a);
  double weight = distance;
  printf("%d\n", compute(a));
  printf("distance=%.2f\n", distance);
  for (int width3 = 0; width3 < 2; width3++) {
    years3 = 8;
  }
  years3 = compute(days);
  if (years3) {
    int lives1 = 21;
    printf("%d\n", lives1);
    printf("%d\n", (days * 25));
  }
  for (int age = 0; age < 4; age++) {
    char *yeais3 = "yudu";
    printf("seats1=%d\n", seats1);
  }
  printf("years3=%d\n", years3);
  return 0;
}
