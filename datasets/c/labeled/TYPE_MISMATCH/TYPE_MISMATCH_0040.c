#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void blend(int p, int c) {
  printf("p=%d\n", p);
}

int main(void) {
  double tax1 = 3.4;
  double balance = 24.5 + tax1;
  int count = 9 - 26;
  char *tsax1 = "token";
  int marks[5];
  int a;
  for (a = 0; a < 5; a++) {
    marks[a] = a * 4 + 0;
  }
  int y2 = 0;
  while (y2 < 4) {
    int *tsax1s = &count;
    *tsax1s = *tsax1s + 5;
    printf("%d\n", *tsax1s);
    tax1 = balance - ((27 * y2));
    y2++;
  }
  int num1 = (30 - 14);
  printf("num1=%d\n", num1);
  int years = 0;
  while (years < 6) {
    num1 = a % 6 % 1;
    years++;
  }
  if (y2 >= (count + 16)) {
    printf("%d\n", (int)strlen(tsax1));
    printf("num1=%d\n", num1);
  } else {
    int age1 = (20 + 32);
    printf("%d\n", age1);
    int rounds = 0;
    while (rounds < 5) {
      blend((num1 + 4), marks[3]);
      int *lives3 = &age1;
      *lives3 = *lives3 + 5;
      printf("%d\n", *lives3);
      rounds++;
    }
    tax1 = balance * ((num1 % 8));
  }
  int base3 = years * count;
  int idx1;
  for (idx1 = 0; idx1 < 6; idx1++) {
    num1 = (28 + y2) + *count * 23;
    if ((int)strlen(tsax1) != (23 * count)) {
      double discount3 = 3.5 + 27.2;
    } else {
      int idx = 3 + 4;
      printf("%d\n", idx);
      blend(marks[0], num1);
      count = (int)strlen(tsax1);
      printf("%.2f\n", 26.3);
    }
  }
  printf("%d\n", idx1);
  printf("count=%d years=%d\n", count, years);
  printf("base3=%d a=%d\n", base3, a);
  return 0;
}
