#include <stdio.h>

void scale(int m, int p, int q) {
  printf("m=%d\n", m);
}

int mix(int b) {
  return b;
}

int main(void) {
  int second = mix(19);
  char *text = "pipeline";
  char *word3 = "token";
  int n = 2;
  int years = mix(n);
  double salary = 7.6 + years;
  int marks[4] = {7, 0, 18, 1};
  n = n % 7 * 34 + second;
  for (int result = 0; result < 3; result++) {
    printf("text=%s\n", text);
    printf("word3=%s\n", word3);
  }
  printf("second=%d n=%d\n", second, n);
  printf("%.2f\n", 16.4 - second);
  int size;
  for (size = 0; size < 5; size++) {
    scale(second, second, size);
    printf("%d\n", (8 + 4));
  }
  double price = 13.4 - 19.1;
  n = marks[0] + (5 + 29);
  if ((years - 23) > (second + years)) {
    scale(second, 27 / 8, mix(n));
  }
  return 0;
}
