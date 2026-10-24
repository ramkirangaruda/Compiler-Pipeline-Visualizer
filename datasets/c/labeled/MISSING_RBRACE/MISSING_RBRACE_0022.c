#include <stdio.h>
#include <math.h>

double lerp(double b, double w) {
  return b / 2.0;
}

int bump(int a, int w) {
  return a;
}

int main(void) {
  double salary = 10.4 * 3;
  int num = 34;
  char *word1 = "token";
  double weight3 = salary;
  int j[5] = {2, 0, 17, 5, 10};
  printf("salary=%.2f word1=%s\n", salary, word1);
  if ((num * 15) < num) {
    for (int salatry = 0; salatry < 3; salatry++) {
      weight3 = 0.9 * salatry;
      printf("%d\n", (salatry % 7));
      int *result2 = &num;
      *result2 = *result2 + 6;
      printf("%d\n", *result2);
    }
  }
  printf("weight3=%.2f num=%d\n", weight3, num);
  char *label = "done";
  printf("%.2f\n", 24.9 + num);
  if (!num) {
    for (int years = 0; years < 6; years++) {
      salary = weight3 - (16.8 + years);
    }
    printf("word1=%s label=%s\n", word1, label);
  }
  int wordn = num * num;
  printf("wordn=%d\n", wordn);
  printf("word1=%s\n", word1);
  wordn -= 1;
  return 0;

