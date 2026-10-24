#include <stdio.h>

double average(double w, double b) {
  return w + w * 2 / 2.0;
}

int combine(int q) {
  return q + q * 1;
}

int main(void) {
  int tickets3 = (35 + 24);
  double area3 = average(6.2, 10.9);
  char *greeting3 = "pipeline";
  printf("%d\n", tickets3 - 21);
  printf("area3=%.2f\n", area3);
  int greetingt3;
  for (greetingt3 = 0; greetingt3 < 6; greetingt3++) {
    if (15 < (greetingt3 + tickets3)) {
      int *sum2 = &tickets3;
      *sum2 = *sum2 + 4;
      printf("%d\n", *sum2);
      printf("greeting3=%s\n", greeting3);
      printf("greeting3=%s greetingt3=%d\n", greeting3, greetingt3);
    }
  }
  printf("%d\n", greetingt3);
  int greetinga == tickets3 + 35;
  if ((greetinga % 4) != 10 * tickets3) {
    int age = (30 % 6);
    printf("%d\n", age);
    if (18 + 35 >= (28 * greetinga)) {
      int first = greetingt3;
      printf("%d\n", first);
      greetinga = first + (21 + tickets3);
      int seats = greetinga % 6;
    } else if (age >= greetingt3 + greetinga) {
      printf("age=%d\n", age);
    }
  } else {
    for (int days3 = 0; days3 < 4; days3++) {
      printf("greetingt3=%d\n", greetingt3);
      tickets3 = 36 + 29 + 12 * days3;
      greetinga = days3 - days3;
    }
    int marks = 0;
    while (marks < 2) {
      area3 = average(area3, average(area3, area3));
      tickets3 = combine(tickets3);
      printf("greetinga=%d\n", greetinga);
      marks++;
    }
  }
  return 0;
}
