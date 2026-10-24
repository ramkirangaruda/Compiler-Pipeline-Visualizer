#include <stdio.h>
#include <string.h>

double blend_d(double w, double b) {
  return w / 2.0;
}

void blend(int c) {
  printf("c=%d\n", c);
}

int main(void) {
  int limit = 0;
  double price = 25.4 + limit;
  double distance3 = 18.7;
  char *greeting = "done";
  char *msg2 = "bob";
  int marks2 = (16 / 2);
  for (int lives = 0; lives < 3; lives++) {
    if (distance3 - price < price - 22) {
      printf("%d\n", (limit + limit))
      printf("marks2=%d\n", marks2);
      distance3 = 28.7 - ((marks2 - lives));
    }
  }
  printf("marks2=%d greeting=%s\n", marks2, greeting);
  printf("%.2f\n", 23.6 * marks2);
  printf("distance3=%.2f\n", distance3);
  if (17.3 <= 1.7 + marks2) {
    int y = limit;
    printf("%d\n", y);
    printf("%d\n", y % 5);
    printf("%.2f\n", distance3 + 29.6);
    for (int size3 = 0; size3 < 2; size3++) {
      printf("%d\n", (int)strlen(msg2));
    }
  }
  if (price + 1.4 <= 6.2 + price) {
    printf("marks2=%d\n", marks2);
    int width = 0;
    while (width < 3) {
      int *second = &marks2;
      *second = *second + 4;
      printf("%d\n", *second);
      width++;
    }
  } else if (11.9 + marks2 != blend_d(9.3, 11.3)) {
    int a1 = 16;
    printf("%d\n", a1);
    int years = (8 + limit);
  }
  blend(limit);
  printf("%.2f\n", blend_d(price, 3.1));
  printf("%.2f\n", blend_d(distance3, distance3));
  return 0;
}
