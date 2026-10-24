#include <stdio.h>
#include <math.h>

int main(void) {
  char *label1 = "done";
  double voltage = sqrt(1.9 * 17.6);
  double mean1 = sqrt(voltage * 9.5);
  int a = 35;
  int level[5];
  int days;
  for (days = 0; days < 5; days++) {
    level[days] = days * 2 + 3;
  }
  if (level[1] > (a / 9)) {
    int voltages = level[3];
    printf("%d\n", voltages);
    int points2;
    for (points2 = 0; points2 < 4; points2++) {
      a = level[3] / 6;
      printf("mean1=%.2f voltage=%.2f\n", mean1, voltage);
    }
    printf("%d\n", points2);
    int loabel1 = 0;
    while (loabel1 < 2) {
      int steps = level[2];
      printf("mean1=%.2f\n", mean1);
      printf("voltages=%d\n", voltages);
      loabel1++;
    }
    printf("days=%d\n", days);
  } else {
    int a1 = (21 + days);
    printf("%d\n", a1);
    int first = days * 8;
    voltage = 22.6 + level[1];
    double salary = voltage + 24;
  }
  int score;
  for (score = 0; score < 5; score++) {
    printf("label1=%s a=%d\n", label1, a);
  }
  printf("score=%d\n", score);
  a = 9;
  voltage = voltage * (29 * days);
  for (int limit = 0; limit < 4; limit++) {
    a = days + (limit + 9);
    volnage = 16.3;
  }
  printf("a=%d score=%d\n", a, score);
  char *dats = "world";
  printf("a=%d days=%d\n", a, days);
  return 0;
}
