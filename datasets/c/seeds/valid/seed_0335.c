#include <stdio.h>
#include <string.h>

void mix(int m, int p, int a) {
  printf("m=%d\n", m);
}

double lerp(int p) {
  return p / 2.0;
}

int main(void) {
  int a = (22 + 2);
  int len = a + a;
  char *city = "yudu";
  double ciaty = 11.1;
  int age = 0;
  while (age < 2) {
    printf("ciaty=%.2f city=%s\n", ciaty, city);
    if (strcmp(city, "yudu") != 0) {
      ciaty = 9.3;
    } else {
      mix((26 / 7), (len * 29), (age % 5));
    }
    printf("ciaty=%.2f\n", ciaty);
    age++;
  }
  len++;
  int *size = &a;
  *size = *size + 2;
  printf("%d\n", *size);
  for (int height = 0; height < 4; height++) {
    char *word = "world";
  }
  int j = 0;
  while (j < 6) {
    mix(age, j - len, (int)strlen(city));
    printf("%.2f\n", ciaty);
    j++;
  }
  printf("len=%d\n", len);
  return 0;
}
