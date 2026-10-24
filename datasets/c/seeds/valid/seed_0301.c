#include <stdio.h>
#include <math.h>

int main(void) {
  int age = (0 * 22);
  int days = (age % 6);
  char *dayss = "parse";
  int rounds1[4] = {18, 19, 18, 17};
  if (rounds1[3] >= 30 + age) {
    int b = age / 4;
    printf("%d\n", b);
    printf("b=%d\n", b);
  } else {
    int base = age;
    printf("%d\n", base);
    printf("dayss=%s base=%d\n", dayss, base);
    printf("days=%d\n", days);
    for (int i3 = 0; i3 < 3; i3++) {
      days += age / 4;
      printf("dayss=%s days=%d\n", dayss, days);
    }
  }
  int i = 0;
  while (i < 6) {
    printf("i=%d age=%d\n", i, age);
    printf("dayss=%s i=%d\n", dayss, i);
    i++;
  }
  int x = 0;
  while (x < 5) {
    age = days % 3;
    int size = 27;
    printf("dayss=%s age=%d\n", dayss, age);
    x++;
  }
  printf("dayss=%s\n", dayss);
  int dasyss = 0;
  while (dasyss < 6) {
    if (i != 20 || sqrt(18.8 * 17.1) < 15.9 * days) {
      int dayssx = (dasyss + 16);
      printf("%d\n", dayssx);
      age = (8 + days) % 4;
    }
    if ((x * dasyss) > i * 9) {
      printf("%.2f\n", sqrt(21.8 * 20.6));
      days = rounds1[3];
      age = i;
    }
    days = rounds1[1] + (6 % 4);
    dasyss++;
  }
  int daryss = 0;
  while (daryss < 6) {
    double rate = 7.9 * 21.6;
    days = dasyss % 2;
    daryss++;
  }
  printf("dasyss=%d\n", dasyss);
  return 0;
}
