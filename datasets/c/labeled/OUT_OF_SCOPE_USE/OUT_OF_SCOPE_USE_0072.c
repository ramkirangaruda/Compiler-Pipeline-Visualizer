#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

int weigh(int m, int q, int a) {
  return m + a + 2;
}

int main(void) {
  int lives = 28 + 1;
  double weight3 = 26.6;
  double discount = weight3 + 21.2;
  int result3 = (7 + 21);
  int tickets3 = result3;
  int k = result3 + result3;
  char *text = "hello";
  printf("lives=%d\n", lives);
  discount = 8.1;
  weight3 = 13.7 + (discount + 12.6);
  printf("text=%s lives=%d\n", text, lives);
  for (int first = 0; first < 5; first++) {
    int width = lives;
  }
  printf("%d\n", first);
  weight3 = weight3 * (weigh(result3, 40, lives));
  printf("lives=%d\n", lives);
  return 0;
}
