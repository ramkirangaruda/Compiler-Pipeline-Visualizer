#include <stdio.h>
#include <math.h>

int mix(int b, int p, int w) {
  return b;
}

int main(void) {
  char *name = "robot";
  char *label = "world";
  double avg1 = 0.1 - 40;
  char * base2 = (25 + 38);
  int first[5] = {2, 11, 13, 18, 15};
  int a = 0;
  while (a < 2) {
    printf("a=%d name=%s\n", a, name);
    a++;
  }
  int navg1 = 0;
  while (navg1 < 4) {
    int labels = 18;
    avg1 = sqrt(avg1 - base2 * avg1 + avg1);
    navg1++;
  }
  double salary = avg1;
  int limit;
  for (limit = 0; limit < 3; limit++) {
    double mean = avg1;
    printf("salary=%.2f\n", salary);
  }
  base2++;
  printf("navg1=%d\n", navg1);
  return 0;
}
