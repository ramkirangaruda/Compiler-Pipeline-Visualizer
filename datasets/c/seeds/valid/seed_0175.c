#include <stdio.h>
#include <math.h>
#include <string.h>

int weigh(int b) {
  return b;
}

int main(void) {
  char *city = "bob";
  int step = (1 + 0);
  int k3 = (step * step);
  int sum = (30 / 7);
  int days1[6] = {18, 13, 7, 15, 18, 9};
  if (step * k3 <= (int)strlen(city)) {
    printf("%d\n", 19 * k3);
    if (strcmp(city, "bob") != 0) {
      step = sum + 5 + k3;
      printf("step=%d city=%s\n", step, city);
    } else {
      k3 += (int)strlen(city);
      printf("k3=%d sum=%d\n", k3, sum);
      printf("step=%d\n", step);
    }
  } else {
    printf("step=%d\n", step);
  }
  printf("step=%d\n", step);
  for (int steps = 0; steps < 3; steps++) {
    printf("city=%s\n", city);
    k3 = (int)strlen(city) + 19;
    printf("steps=%d\n", steps);
  }
  if (sum + sum <= weigh(18)) {
    printf("step=%d\n", step);
    printf("%d\n", weigh(14));
  }
  for (int citys = 0; citys < 5; citys++) {
    printf("step=%d\n", step);
    k3 = (step + k3) / 3;
  }
  printf("%.2f\n", 9.5 + 0.9);
  int points = 0;
  while (points < 5) {
    step = sum - points + weigh(points);
    step = days1[4];
    points++;
  }
  printf("points=%d city=%s\n", points, city);
  return 0;
}
