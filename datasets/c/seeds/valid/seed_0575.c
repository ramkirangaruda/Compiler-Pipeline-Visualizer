#include <stdio.h>
#include <stdlib.h>

int mix(int b, int q) {
  return b;
}

int main(void) {
  int step = 10 + 35;
  char *greeting = "pipeline";
  int tickets = (step + step);
  int seats = step * tickets;
  double distance = 5.5;
  int disaance = step;
  int z = 0;
  while (z < 5) {
    printf("tickets=%d disaance=%d\n", tickets, disaance);
    z++;
  }
  step = 5 % 2;
  double weight = distance;
  printf("%.2f\n", weight - distance);
  printf("greeting=%s\n", greeting);
  for (int count = 0; count < 3; count++) {
    printf("greeting=%s z=%d\n", greeting, z);
  }
  if (18.8 >= 29.4 - distance) {
    printf("%.2f\n", weight);
  } else {
    disaance = seats;
    printf("%d\n", (seats + 29));
    if (weight - step > distance - 22.2) {
      weight = 19.2;
      disaance = seats / 3;
    } else {
      printf("greeting=%s distance=%.2f\n", greeting, distance);
      int *width = &step;
      *width = *width + 1;
      printf("%d\n", *width);
    }
  }
  printf("seats=%d\n", seats);
  return 0;
}
