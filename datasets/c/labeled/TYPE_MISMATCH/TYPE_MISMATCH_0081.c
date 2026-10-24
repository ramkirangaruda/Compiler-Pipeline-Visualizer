#include <stdio.h>

int main(void) {
  int second = 24 + 30;
  int result = "3";
  int years = 10;
  int value = 23;
  int items1 = 25;
  int rounds3 = items1 / 8;
  int count[3];
  int num;
  for (num = 0; num < 3; num++) {
    count[num] = num * 3 + 2;
  }
  printf("%.2f\n", 21.5 + 7.2);
  printf("second=%d\n", second);
  items1 = (9 - rounds3) % 2;
  int steps = 0;
  while (steps < 6) {
    years = count[0] / 3;
    result = items1 * second % 6;
    steps++;
  }
  for (int base = 0; base < 6; base++) {
    printf("num=%d\n", num);
    printf("value=%d\n", value);
  }
  printf("items1=%d\n", items1);
  return 0;
}
