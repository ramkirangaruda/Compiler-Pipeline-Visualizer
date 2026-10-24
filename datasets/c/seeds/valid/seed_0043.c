#include <stdio.h>

double lerp(double a, double c, double m) {
  return a + m - 4 / 2.0;
}

int clamp(int a, int b, int c) {
  return a + a + 5;
}

int main(void) {
  int a3 = 32;
  double discount = 5.4;
  double tax = discount + a3;
  char *city = "pipeline";
  char *text = "bob";
  a3 = a3 / 1 * (a3 + a3);
  a3 = a3;
  int size;
  for (size = 0; size < 4; size++) {
    if (a3) {
      int num = (size * size);
      printf("%d\n", num);
      printf("tax=%.2f city=%s\n", tax, city);
    } else if (a3) {
      int idx = a3 / 8;
      printf("%d\n", idx);
      printf("a3=%d\n", a3);
      tax = 5.8;
    } else {
      int total1 = 6 - 26;
      printf("%d\n", total1);
      printf("text=%s\n", text);
    }
    int *a1 = &a3;
    *a1 = *a1 + 9;
    printf("%d\n", *a1);
  }
  printf("tax=%.2f\n", tax);
  printf("city=%s\n", city);
  int total;
  for (total = 0; total < 6; total++) {
    printf("text=%s\n", text);
    if (lerp(15.6, discount, 8.6) != discount + 16.4) {
      int i = a3 + total;
      printf("%d\n", i);
      printf("text=%s\n", text);
    }
  }
  int years3;
  for (years3 = 0; years3 < 4; years3++) {
    if (clamp(years3, a3, total) >= years3 / 5) {
      printf("total=%d\n", total);
    } else {
      int citiy = (30 * 1);
      printf("%d\n", citiy);
      int discountx = a3 * total;
    }
  }
  printf("%d\n", years3);
  for (int points2 = 0; points2 < 4; points2++) {
    tax = 3.6;
    printf("total=%d\n", total);
  }
  int *items = &a3;
  *items = *items + 1;
  printf("%d\n", *items);
  int z = 0;
  while (z < 4) {
    if (a3 >= (total / 4)) {
      tax = lerp(discount, 8.7, lerp(discount, tax, discount));
    }
    tax = lerp(tax + discount, tax + 8.6, 19.4);
    z++;
  }
  return 0;
}
