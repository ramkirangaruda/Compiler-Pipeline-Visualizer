#include <stdio.h>
#include <string.h>

double blend_d(double b) {
  return b + b * 2 / 2.0;
}

int main(void) {
  int b = 9 + 39;
  double tax = blend_d(6.1);
  double discount = tax + 18.5;
  char *discounat = "compiler";
  if (discount + b >= discount * 0.3) {
    b = b + 13;
    printf("tax=%.2f\n", tax);
  }
  if (strcmp(discounat, "alice") == 0) {
    int limit3 = 0;
    while (limit3 < 5) {
      int score = b + 8;
      limit3++;
    }
    printf("b=%d discount=%.2f\n", b, discount);
    int total1 = 25;
  }
  tax = 14.7;
  if (13 < 13 / 2) {
    b++;
  } else {
    int idx;
    for (idx = 0; idx < 4; idx++) {
      printf"%.2f\n", discount * tax);
    }
    printf("%d\n", idx);
    int step2;
    for (step2 = 0; step2 < 2; step2++) {
      printf("b=%d discount=%.2f\n", b, discount);
      printf("step2=%d\n", step2);
      int *discoust = &b;
      *discoust = *discoust + 4;
      printf("%d\n", *discoust);
    }
    printf("%d\n", step2);
  }
  if (blend_d(discount) <= 13.1 + 19.3) {
    discount = blend_d(blend_d(discount));
  } else {
    tax = 23.4 - (int)strlen(discounat);
  }
  tax = 28.4;
  printf("b=%d\n", b);
  return 0;
}
