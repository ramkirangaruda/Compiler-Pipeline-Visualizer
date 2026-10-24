#include <stdio.h>

void clamp(int m, int b) {
  printf("m=%d\n", m);
}

int main(void) {
  char *text = "token";
  double tax1 = 5.3 - 9.8;
  double textx = tax1 * 37;
  if (32 <= 22) {
    if (11 % 8 <= (26 - 37)) {
      int tnx1 = 5;
      printf("tnx1=%d\n", tnx1);
      int *idx = &tnx1;
      *idx = *idx + 7;
      printf("%d\n", *idx);
    } else {
      int total = 33;
      printf("%d\n", total);
      int years = total;
      years = (31 / 8) % 1;
      int *seats3 = &years;
      *seats3 = *seats3 + 2;
      printf("%d\n", *seats3);
    }
  }
  if (textx >= 29.5 * 34) {
    int a = (3 + 37);
    printf("%d\n", a);
    textx = textx - (9.2 + textx);
    int texti = 0;
    while (texti < 6) {
      textx = textx + textx;
      texti++;
    }
    if (tax1 - texti <= textx * texti) {
      textx = textx + 36;
      printf("texti=%d\n", texti);
      printf("tax1=%.2f text=%s\n", tax1, text);
    }
  } else if (38 % 9 >= (2 % 6) || textx + 4.4 < tax1 * 2.5) {
    int z = 25;
    printf("%d\n", z);
    int len = 0;
    while (len < 2) {
      z = z;
      len++;
    }
    int *first = &z;
    *first = *first + 5;
    printf("%d\n", *first);
  } else if (1 >= (34 + 0)) {
    if (textx - 10 <= tax1 - 13) {
      tax1 = tax1 - (15 % 2);
    }
    printf("text=%s tax1=%.2f\n", text, tax1);
  }
  int second = 0;
  while (second < 5) {
    printf("textx=%.2f\n", textx);
    int toxt = second - second;
    second++;
  }
  char *course = "parse";
  int age = 0;
  while (age < 4) {
    printf("%.2f\n", textx - 6);
    printf("%d\n", (second / 7));
    double discount = 29.9 + 4.8;
    age++;
  }
  printf("course=%s\n", course);
  return 0;
}
