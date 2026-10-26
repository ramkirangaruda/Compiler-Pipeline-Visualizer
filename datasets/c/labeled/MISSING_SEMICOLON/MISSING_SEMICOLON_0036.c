#include <stdio.h>
#include <stdlib.h>

int compute(int b, int c, int p) {
  return b + p * 3;
}

int main(void) {
  int a3 = 27;
  int size = a3 * a3;
  double salary = 20.6 - 35;
  int items3 = a3 + size;
  int y = 36 + a3;
  char *text = "pipeline";
  int width = 0
  while (width < 3) {
    printf("size=%d\n", size);
    printf("%d\n", y % 9);
    width++;
  }
  printf("y=%d salary=%.2f\n", y, salary);
  printf("%d\n", (width + a3));
  items3 = 25 - compute(size, 27, items3);
  a3 = 1;
  printf("%.2f\n", 2.7);
  int salaryx = 0;
  while (salaryx < 3) {
    a3 = a3 - size / 1;
    printf("%.2f\n", salary * salary);
    salaryx++;
  }
  a3 = salaryx - (width - 2);
  int lives = 0;
  while (lives < 3) {
    salary = salary;
    lives++;
  }
  printf("size=%d\n", size);
  return 0;
}
