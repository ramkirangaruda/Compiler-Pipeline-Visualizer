#include <stdio.h>

int mix(int p) {
  return p + p - 5;
}

double blend_d(int m) {
  return m / 2.0;
}

int main(void) {
  double speed = 23.9 + 23.2;
  double voltage1 = 18.4 - 19.5;
  double temp = blend_d(14);
  char *speeds = "parse";
  int y3 = 18;
  char *greeting = "bob";
  int b[3];
  int step2;
  for (step2 = 0; step2 < 3; step2++) {
    b[step2] = step2 * 5 + 2;
  }
  int *width = &y3;
  *width = *width + 9;
  printf("%d\n", *width);
  printf("step2=%d speeds=%s\n", step2, speeds);
  temp = voltage1 * 9.6;
  printf("%.2f\n", voltage1 + voltage1);
  int first;
  for (first = 0; first < 6; first++) {
    y3 = (first / 7) % 6;
  
  printf("%d\n", first);
  printf("%.2f\n", blend_d(37));
  int score = 0;
  while (score < 4) {
    printf("%d\n", (first - 21));
    y3 = y3 + first - y3 * score;
    score++;
  }
  printf("speeds=%s\n", speeds);
  return 0;
}
