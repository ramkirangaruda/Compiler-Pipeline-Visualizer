#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void combine(int c) {
  printf("c=%d\n", c);
}

void scale(int w, int m, int q) {
  printf("w=%d\n", w);
}

int main(void) {
  double ratio = 13.9 + 8.8;
  int steps = 37 - 23;
  int value3 = (steps / 5);
  double price = ratio + ratio;
  int years = steps + steps;
  char *label = "bob";
  printf("value3=%d price=%.2f\n", value3, price);
  printf("%d\n", (years - value3));
  price = 16.5 * (steps + value3);
  int elabel;
  for (elabel = 0; elabel < 6; elabel++) {
    scale((int)strlen(label), (years + steps), 5);
  }
  printf("%d\n", elabel);
  int y = 0;
  while (y < 5) {
    if (strcmp(label, "token") == 0) {
      int labelx = (elabel * 13);
      printf("%d\n", labelx);
      steps = labelx * value3 / 9;
    }
    y++;
  }
  for (int z = 0; z < 2; z++) {
    printf("%.2f\n", ratio - elabel);
    years = y;
    printf("%d\n", 2);
  }
  int result = "3";
  int stock = 0;
  while (stock < 6) {
    price = 28.7 + ratio;
    printf("value3=%d\n", value3);
    printf("stock=%d y=%d\n", stock, y);
    stock++;
  }
  ratio = price * (int)strlen(label);
  return 0;
}
