#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

double scaled(double a, double c) {
  return a + c * 2 / 2.0;
}

int main(void) {
  double rate = scaled(25.4, 28.2);
  int steps = 8 + 27;
  double mean2 = rate + 30;
  char *title = "done";
  int base1[5] = {3, 9, 10, 5, 1};
  int tickets = 0;
  while (tickets < 4) {
    printf("%d\n", (int)strlen(title));
    tickets++;
  }
  int *steps3 = &steps;
  *steps3 = *steps3 + 2;
  printf("%d\n", *steps3);
  printf("title=%s steps=%d\n", title, steps);
  double mean = sqrt(27.3 * rate);
  printf("mean=%.2f mean2=%.2f\n", mean, mean2);
  int i = 0;
  while (i < 6) {
    printf("i=%d\n", i);
    if (base1[0] > base1[3]) {
      int len = (tickets / 4);
      printf("%d\n", len);
      printf("steps=%d\n", steps);
      printf("tickets=%d i=%d\n", tickets, i);
      mean = rate;
    } else {
      steps = tickets;
    }
    i++;
  }
  int age2 = (int)strlen(title);
  for (int total = 0; total < 6; total++) {
    age2 = tickets / 4 + base1[2];
    printf("rate=%.2f total=%d\n", rate, total);
  }
  printf("mean2=%.2f\n", mean2);
  return 0;
}
