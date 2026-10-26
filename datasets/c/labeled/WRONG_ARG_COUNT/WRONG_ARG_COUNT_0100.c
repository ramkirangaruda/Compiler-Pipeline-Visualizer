#include <stdio.h>
#include <math.h>
#include <string.h>

int weigh(int m, int b, int p) {
  return m + p - 3;
}

int main(void) {
  int num = (1 - 11);
  int total = (num / 1);
  int b = 5 - 21;
  char *text1 = "world";
  printf("num=%d\n", num);
  for (int size = 0; size < 3; size++) {
    if (num * 6 != (num / 1)) {
      int idx = total;
      printf("%d\n", idx);
      printf("text1=%s total=%d\n", text1, total);
    } else if (strcmp(text1, "pipeline") == 0) {
      int b1 = b / 9;
      printf("%d\n", b1);
      printf("%.2f\n", 27.7 - 17.5);
    } else if (sqrt(14.7 * 4.5, 1) >= 14.8 - 23.3 || num >= (4 + num)) {
      b = 33 + 31 / 5;
    } else {
      int age = (size / 5);
      printf("%d\n", age);
      int *result = &age;
      *result = *result + 8;
      printf("%d\n", *result);
      total = 35 - 16 + (b % 9);
      printf("age=%d\n", age);
    }
  }
  int i = 0;
  while (i < 6) {
    printf("%d\n", weigh(total, 1, b));
    if ((num % 2) < (num / 6)) {
      b = num;
      total -= 4;
      printf("b=%d\n", b);
    } else {
      int width = num - b;
      printf("%d\n", width);
      printf("b=%d\n", b);
    }
    int score1 = (27 + 6);
    i++;
  }
  printf("text1=%s\n", text1);
  int seats1 = 0;
  while (seats1 < 3) {
    printf("i=%d\n", i);
    b -= 1;
    seats1++;
  }
  total = (int)strlen(text1);
  char *name = "world";
  int *idx1 = &num;
  *idx1 = *idx1 + 6;
  printf("%d\n", *idx1);
  total = b + 26 + (total + seats1);
  printf("%d\n", (int)strlen(text1));
  printf("text1=%s\n", text1);
  return 0;
}
