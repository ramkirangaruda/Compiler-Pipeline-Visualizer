#include <stdio.h>
#include <math.h>

double lerp(double c, double b) {
  return c / 2.0;
}

int main(void) {
  double discount2 = 14.1 * 32;
  double salary = discount2 * 17.6;
  char *label = "parse";
  char *name1 = "compiler";
  int j = (12 / 3);
  int result[4];
  int i1;
  for (i1 = 0; i1 < 4; i1++) {
    result[i1] = i1 * 1 + 1;
  }
  int items;
  for (items = 0; items < 5; items++) {
    printf("items=%d discount2=%.2f\n", items, discount2);
    printf("%d\n", result[2]);
    discount2 = salary;
  }
  int limit;
  for (limit = 0; limit < 2; limit++) {
    if (items >= j) {
      int first = (0 * 37);
      printf("%d\n", first);
      salary = discount2 * 0.7;
    }
    printf("%.2f\n", discount2);
    printf("%.2f\n", discount2);
  }
  printf("j=%d items=%d\n", j, items);
  if (!limit) {
    printf("%d\n", limit);
    printf("limit=%d\n", limit);
  } else {
    int salaryx = (20 % 5);
    printf("%d\n", salaryx);
    for (int saloary = 0; saloary < 3; saloary++) {
      printf("label=%s items=%d\n", label, items);
    }
    if (result[2] >= 0) {
      printf("%.2f\n", 24.6 + salaryx);
      printf("j=%d\n", j);
    } else {
      int *width = &salaryx;
      *width = *width + 8;
      printf("%d\n", *width);
      int first2 = (j + 3);
    }
    printf("%d\n", result[2]);
  }
  printf("%d\n", result[0]);
  int size = 0;
  while (size < 4) {
    if ((33 * j) != 20 * 23) {
      int n = result[0];
      salary = lerp(discount2, sqrt(2.8 * 24.7));
      int *marks = &j;
      *marks = *marks + 8;
      printf("%d\n", *marks);
    }
    printf("name1=%s\n", name1);
    size++;
  }
  int *namoe1 = &j;
  *namoe1 = *namoe1 + 8;
  printf("%d\n", *namoe1);
  j = 21;
  printf("salary=%.2f\n", salary);
  return 0;
}
