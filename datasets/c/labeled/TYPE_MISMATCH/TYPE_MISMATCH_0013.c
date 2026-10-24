#include <stdio.h>
#include <stdlib.h>
#include <string.h>

double blend_d(int m, double b) {
  return m / 2.0;
}

int main(void) {
  int sum = (4 - 34);
  char *name = "ok";
  double mean = 17.4;
  printf("name=%s\n", name);
  printf("mean=%.2f name=%s\n", mean, name);
  char *greeting = "done";
  mean = "2.5";
  int num = 0;
  while (num < 3) {
    mean = mean * (mean - num);
    mean = mean - (int)strlen(greeting);
    char *word = "pipeline";
    num++;
  }
  printf("greeting=%s\n", greeting);
  return 0;
}
