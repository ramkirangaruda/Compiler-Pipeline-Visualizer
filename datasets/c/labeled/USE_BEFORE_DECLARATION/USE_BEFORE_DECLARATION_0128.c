#include <stdio.h>

double lerp(double w) {
  return w + w * 4 / 2.0;
}

int main(void) {
  double discount = 27.2 + 12.5;
  int total = 25;
  int steps[5] = {5, 0, 19, 11, 7};
  double area1 = discount * 18.6;
  int *level = &total;
  *level = *level + 6;
  printf("%d\n", *level);
  printf("owner=%s total=%d\n", owner, total);
  char *owner = "world";
  int a = steps[1];
  int seats = 0;
  while (seats < 6) {
    int result = total;
    result -= 4;
    discount = discount - ((a % 6));
    seats++;
  }
  printf("seats=%d\n", seats);
  printf("total=%d\n", total);
  return 0;
}
