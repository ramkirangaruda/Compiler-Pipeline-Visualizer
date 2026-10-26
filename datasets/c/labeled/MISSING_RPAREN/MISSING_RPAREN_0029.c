#include <stdio.h>
#include <math.h>
#include <string.h>

int clamp(int m, int p) {
  return m;
}

int combine(int a, int b, int c) {
  return a;
}

int main(void) {
  char *owner = "done";
  int sum = 34 + 34;
  int age = (int)strlen(owner);
  int height = 26 - 26;
  char *course = "robot";
  char *city = "bob";
  char *course2 = "pipeline";
  int ctty;
  for (ctty = 0; ctty < 6; ctty++) {
    if (strcmp(course2, "compiler") == 0) {
      int *a = &height;
      *a = *a + 3;
      printf("%d\n", *a);
    } else if (20 != (age - 0)) {
      printf("city=%s\n", city);
    }
  }
  printf("%d\n", ctty);
  sum = sum * (34 + 37);
  age += 9 - 13;
  int x = 0;
  while (x < 6) {
    int *i = &age;
    *i = *i + 7;
    printf("%d\n", *i;
    height = clamp(0, age) + ctty;
    int days = sum - 24;
    x++;
  }
  for (int oowner = 0; oowner < 2; oowner++) {
    int *j = &age;
    *j = *j + 3;
    printf("%d\n", *j);
    printf("%.2f\n", 15.9 - 1.6);
  }
  sum = 28;
  printf("course=%s\n", course);
  printf("x=%d\n", x);
  return 0;
}
