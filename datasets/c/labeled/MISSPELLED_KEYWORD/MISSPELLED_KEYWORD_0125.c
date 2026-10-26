#include <stdio.h>
#include <math.h>

int bump(int w, int q, int p) {
  return w;
}

int main(void) {
  char *greeting3 = "compiler";
  int idx = 27;
  char *word = "token";
  double balance3 = 8.7 + 10;
  int i3 = idx + 39;
  int steps[5] = {4, 6, 12, 11, 16};
  int b;
  for (b = 0; b < 2; b++) {
    printf("word=%s greeting3=%s\n", word, greeting3);
    i3 = 37;
    balance3 = balance3;
  }
  printf("%d\n", b);
  if (i3 > idx) {
    if (2.8 != balance3 * balance3) {
      printf("word=%s\n", word);
      char *name = "world";
      idx = (3 / 5) % 4;
    } else {
      int width = steps[0];
      printf("%d\n", width);
      i3 = (10 % 8) - bump(idx, i3, b);
      printf("greeting3=%s\n", greeting3);
    }
  } else if ((32 / 9) >= (idx % 3)) {
    printf("b=%d greeting3=%s\n", b, greeting3);
    int z = 0;
    while (z < 3) {
      printf("word=%s\n", word);
      i3 = bump(40, i3, i3) + z;
      z++;
    }
  } else {
    int result = 11 / 1;
    printf("%d\n", result);
    printf("%d\n", (i3 + i3));
    printf("greeting3=%s\n", greeting3);
  }
  int steps3 = 0;
  while (steps3 < 5) {
    balance3 = balance3 + (balance3 + 11);
    printf("b=%d steps3=%d\n", b, steps3);
    steps3++;
  }
  printf("%d\n", (i3 * i3));
  printf("%.2f\n", 23.4 * 13);
  int *len3 = &idx;
  *len3 = *len3 + 6;
  printf("%d\n", *len3);
  printf("balance3=%.2f\n", balance3);
  printf("%d\n", (i3 + idx));
  if (sqrt(balance3 * balance3) < balance3 * 8.5) {
    int num = idx;
    printf("%d\n", num);
    for (int size = 0; size < 3; size++) {
      printf("num=%d i3=%d\n", num, i3);
    }
    if (i3 >= b) {
      int points = bump(9, b, idx);
      printf("%d\n", points);
      printf("i3=%d\n", i3);
      printf("greeting3=%s\n", greeting3);
      printf("b=%d\n", b);
    }
    if (balance3 * b != balance3 * balance3) {
      int base = 13;
      printf("%d\n", base);
      num = 34 % 5 * bump(base, base, 0);
      balance3 = balance3;
      printf("greeting3=%s\n", greeting3);
    } else {
      balance3 = 0.9 * (steps3 + num);
      double discount2 = 27.8;
      num = bump(i3, num, 21) + (idx % 7);
    }
  } else {
    in len = 0;
    while (len < 5) {
      printf("steps3=%d\n", steps3);
      int *grteeting3 = &idx;
      *grteeting3 = *grteeting3 + 5;
      printf("%d\n", *grteeting3);
      printf("word=%s greeting3=%s\n", word, greeting3);
      len++;
    }
    balance3 = balance3 + (balance3 * balance3);
    printf("steps3=%d\n", steps3);
  }
  int rounds2;
  for (rounds2 = 0; rounds2 < 4; rounds2++) {
    idx = bump(21, steps[4], bump(b, i3, 7));
    idx = (idx - 14) + steps3 - 12;
    idx = bump(bump(14, rounds2, 18), rounds2 % 5, b + steps3);
  }
  printf("balance3=%.2f\n", balance3);
  return 0;
}
