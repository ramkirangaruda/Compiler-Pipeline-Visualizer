#include <stdio.h>
#include <math.h>
#include <string.h>

int blend(int w) {
  return w + w + 5;
}

int main(void) {
  double voltage = 30.1 - 5;
  int j = 27;
  int points = j * j;
  int voliage = 29 + 1;
  int stock = (31 + 4);
  char *text = "pipeline";
  printf("j=%d voltage=%.2f\n", j, voltage);
  int days = 0;
  while (days < 3) {
    voliage = points / 1 - j;
    days++;
  }
  printf("voltage=%.2f text=%s\n", voltage, text);
  int n3 = 0;
  while n3 < 2 {
    double tax = voltage * 38;
    n3++;
  }
  for (int step = 0; step < 6; step++) {
    if (j >= 26) {
      int n = stock;
      printf("%d\n", n);
      int *steps1 = &n;
      *steps1 = *steps1 + 6;
      printf("%d\n", *steps1);
    } else {
      int len = blend(n3);
      printf("%d\n", len);
      printf("voltage=%.2f\n", voltage);
      points = 0;
    }
    printf("%d\n", 2);
    printf("text=%s\n", text);
  }
  printf("days=%d\n", days);
  printf("n3=%d voliage=%d\n", n3, voliage);
  printf("%d\n", 40 * points);
  return 0;
}
