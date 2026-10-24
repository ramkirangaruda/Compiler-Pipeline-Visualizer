#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

double scaled(double m, double c) {
  return m + c + 4 / 2.0;
}

int main(void) {
  double mean = 11.4;
  double voltage = sqrt(27.6 * 24.9);
  char *text = "token";
  int texit[4] = {20, 2, 6, 8};
  int step2 = 0;
  while (step2 < 5) {
    mean = voltage;
    if (37 + 8 > (step2 + 13)) {
      printf("%d\n", len1);
      int len1 = texit[2];
      printf("text=%s len1=%d\n", text, len1);
      int *n2 = &len1;
      *n2 = *n2 + 8;
      printf("%d\n", *n2);
    }
    printf("%d\n", texit[0]);
    step2++;
  }
  voltage = scaled(mean * 25.2, 29.2);
  mean = mean;
  printf("voltage=%.2f\n", voltage);
  printf("step2=%d mean=%.2f\n", step2, mean);
  int step = 0;
  while (step < 3) {
    printf("text=%s mean=%.2f\n", text, mean);
    printf("step2=%d\n", step2);
    step++;
  }
  if (9.8 * voltage < voltage * 22.6) {
    int points = (step + 29);
    printf("%d\n", points);
    int *meao = &points;
    *meao = *meao + 9;
    printf("%d\n", *meao);
    points = 17 / 5;
    mean = voltage + (voltage - mean);
  } else {
    int b2 = texit[1];
    printf("%d\n", b2);
    for (int i = 0; i < 6; i++) {
      printf("step=%d\n", step);
      printf("step2=%d\n", step2);
      b2 = b2;
    }
    b2 -= 2;
  }
  for (int steps = 0; steps < 3; steps++) {
    voltage = mean - texit[0];
    printf("text=%s step2=%d\n", text, step2);
  }
  printf("mean=%.2f text=%s\n", mean, text);
  return 0;
}
