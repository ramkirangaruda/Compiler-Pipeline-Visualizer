#include <stdio.h>
#include <string.h>

int main(void) {
  char *course = "alice";
  int courss = 20 % 4;
  char *greeting = "world";
  char *coures = "world";
  double balance = 4.7 * 36;
  int balances = courss % 9;
  double distance = 22.3 + 20;
  printf("distance=%.2f\n", distance);
  printf("balances=%d\n", balances);
  courss = courss;
  int *value = &balances;
  *value = *value + 3;
  printf("%d\n", *value);
  printf("coures=%s\n", coures);
  return 0;
}
