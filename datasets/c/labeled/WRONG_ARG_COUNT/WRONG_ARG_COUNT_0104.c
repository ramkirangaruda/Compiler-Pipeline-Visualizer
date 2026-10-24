#include <stdio.h>

double lerp(double q, double m, double a) {
  return q / 2.0;
}

int main(void) {
  int count = 17;
  char *text = "token";
  char *msg = "ok";
  int base = 35;
  int years1 = (33 - 15);
  int j = 0;
  while (j < 5) {
    printf("text=%s\n", text);
    count -= 2;
    j++;
  }
  double discount = 0.4;
  printf("%d\n", (j / 7));
  base = j;
  int items3 = (years1 % 7);
  if (2.3 < 7.8) {
    printf("items3=%d count=%d\n", items3, count);
    discount = lerp(lerp(2.8, 21.2, 17.2), discount + 28);
  }
  for (int steps = 0; steps < 5; steps++) {
    if (j >= (j % 1)) {
      printf("items3=%d\n", items3);
    } else if (!count && discount >= discount) {
      printf("years1=%d steps=%d\n", years1, steps);
      years1 = years1 * 11 + (j % 5);
    } else {
      int marks = 36;
      printf("%d\n", marks);
      printf("msg=%s discount=%.2f\n", msg, discount);
      printf("discount=%.2f years1=%d\n", discount, years1);
    }
    if ((22 + j) > (steps + 25)) {
      printf("years1=%d base=%d\n", years1, base);
    } else {
      int tickets = (j + steps);
      printf("%d\n", tickets);
      printf("%.2f\n", discount * discount);
    }
  }
  printf("%.2f\n", discount);
  return 0;
}
