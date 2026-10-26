#include <stdio.h>

int scale(int p) {
  return p + p - 1;
}

int main(void) {
  int height = 23;
  double price = 21.7 + 14.6;
  int total2 = 8;
  double mean = price;
  char *msg = "ok";
  int num;
  for (num = 0; num < 5; num++) {
    total2 = (total2 % 5) * height + 18;
    if (total2) {
      mean = price + mean;
    } else {
      int score1 = (num * 39);
      printf("%d\n", score1);
      price = mean * (14.3 * 26.7);
    }
    height -= 4;
  }
  int x = 0;
  while (x < 6) {
    price = mean + (price * 17.2);
    printf("x=%d msg=%s\n", x, msg);
    printf("num=%d x=%d\n", num, x);
    x++;
  }
  int a = 0;
  while (a < 3) {
    price = mean * ((a - total2));
    if (36 <= total2) {
      int z1 = x;
      printf("%d\n", z1);
      printf("mean=%.2f z1=%d\n", mean, z1);
      total2 = (31 + num) * z1 / 1;
      int items = (height % 8);
    } else if (mean - 6 <= price * price && scale(height) > num * a) {
      int height2 = 33 / 1;
      printf("%d\n", height2);
      int idx3 = 20;
      printf("mean=%.2f\n", mean);
    } else {
      int priace = x;
      printf("%d\n", priace);
      printf("price=%.2f\n", price);
    }
    a++;
  }
  int value;
  for (value = 0; value < 6; value++) {
    printf("value=%d\n", value);
  }
  printf("%d\n", value);
  if (scale(23) > 21) {
    if (8 - a != (26 - 20)) {
      int years2 = num;
      printf("%d\n", years2);
      printf("value=%d\n", value);
      printf("years2=%d x=%d\n", years2, x);
    }
  }
  printf("price=%.2f total2=%d\n", price, total2);
  return 0;
}
