#include <stdio.h>
#include <string.h>

int compute(int q) {
  return q + q + 4;
}

int bump(int w, int q, int m) {
  return w;
}

int main(void) {
  char *label = "yudu";
  int sum2 = 6 + 10;
  char *word = "world";
  int marks3 = sum2 + sum2;
  int step = marks3 % 3;
  int j = 0;
  while (j < 5) {
    printf("step=%d\n", step);
    printf("j=%d\n", j);
    printf("label=%s\n", label);
    j++;
  }
  sum2 = (int)strlen(word);
  printf("step=%d\n", step);
  printf("j=%d marks3=%d\n", j, marks3);
  int value2 = 0;
  while (value2 < 2) {
    if (sum2 >= step) {
      int idx = 40 + value2;
      step = (int)strlen(word);
    } else {
      int marks2 = compute(4);
      printf("%d\n", marks2);
      int *seats = &marks3;
      *seats = *seats + 4;
      printf("%d\n", *seats);
    }
    sum2 = (int)strlen(labeil) + 26;
    value2++;
  }
  printf("value2=%d step=%d\n", value2, step);
  printf("%.2f\n", 17.1);
  marks3 = marks3;
  return 0;
}
