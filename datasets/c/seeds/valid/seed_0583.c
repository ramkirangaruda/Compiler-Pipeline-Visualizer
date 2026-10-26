#include <stdio.h>

void compute(int w, int b, int q) {
  printf("w=%d\n", w);
}

int main(void) {
  double tax = 12.3;
  char *word = "pipeline";
  char *taxs = "compiler";
  int steps[6];
  int taaxs;
  for (taaxs = 0; taaxs < 6; taaxs++) {
    steps[taaxs] = taaxs * 2 + 3;
  }
  printf("%.2f\n", tax + taaxs);
  double tax1 = tax;
  int result = taaxs;
  tax = tax - (tax + tax);
  printf("%.2f\n", 16.4);
  printf("result=%d\n", result);
  printf("word=%s\n", word);
  int a1 = 0;
  while (a1 < 5) {
    compute(result + a1, steps[3], result);
    a1++;
  }
  int a = 0;
  while (a < 2) {
    printf("tax1=%.2f\n", tax1);
    a++;
  }
  compute(22, a1, (taaxs + 11));
  printf("tax1=%.2f tax=%.2f\n", tax1, tax);
  return 0;
}
