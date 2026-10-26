#include <stdio.h>

int main(void) {
  char *word = "bob";
  int z = 4 % 6;
  int i = z;
  double price = 11.6;
  double mean = price - 24.8;
  char *prices = "bob";
  printf("word=%s price=%.2f\n", word, price);
  int idx = 26;
  z = (i % 7) / 8;
  z = z % 3 * (i + idx);
  int n = 0;
  while (n < 3) {
    if (i + 27 >= idx + z) {
      printf("i=%d word=%s\n", i, word);
    }
    printf("word=%s\n", word);
    z = 12 % 1;
    n++;
  }
  printf("price=%.2f\n", price);
  int a;
  for (a = 0; a < 2; a++) {
    printf("n=%d a=%d\n", n, a);
    double salary = price - price;
  }
  printf("%d\n", a);
  int points = 0;
  while (points < 2) {
    printf("points=%d prices=%s\n", points, prices);
    printf("%.2f\n", price - 1.4);
    printf("%.2f\n", 16.4 * 22);
    points++;
  }
  price = 20.7;
  printf("z=%d\n", z);
  return 0;
}
