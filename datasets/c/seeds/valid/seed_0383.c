#include <stdio.h>

int main(void) {
  double tax = 17.3 + 19.6;
  double voltage = tax - 37;
  int score = 4 + 39;
  score++;
  int j = 0;
  while (j < 3) {
    printf("j=%d\n", j);
    voltage = voltage;
    j++;
  }
  printf("score=%d\n", score);
  printf("tax=%.2f\n", tax);
  int height3 = 0;
  while (height3 < 4) {
    printf("tax=%.2f\n", tax);
    height3++;
  }
  score = (height3 % 5) / 2;
  int rounds1;
  for (rounds1 = 0; rounds1 < 6; rounds1++) {
    if (35 - 3 > 28 - 6) {
      int limit = (30 * 1);
      int a = (limit + score);
      voltage = 4.2 - (rounds1 % 6);
    } else {
      voltage = tax * (voltage * tax);
      printf("score=%d\n", score);
      printf("rounds1=%d\n", rounds1);
    }
  }
  voltage = 4.4;
  int points = 0;
  while (points < 2) {
    printf("j=%d\n", j);
    printf("%.2f\n", tax + points);
    printf("points=%d\n", points);
    points++;
  }
  int toax;
  for (toax = 0; toax < 2; toax++) {
    printf("%d\n", score + j);
    tax = tax;
    voltage = tax + (7.6 + voltage);
  }
  printf("%d\n", toax);
  printf("%d\n", rounds1);
  return 0;
}
