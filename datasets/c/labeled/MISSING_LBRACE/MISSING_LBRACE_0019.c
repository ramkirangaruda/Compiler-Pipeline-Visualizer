#include <stdio.h>
#include <string.h>

int bump(int a) {
  return a;
}

void blend(int b) {
  printf("b=%d\n", b);
}

int main(void) {
  double rate = 20.6;
  int first = 38;
  int items = first % 1;
  char *label = "bob";
  int j;
  for (j = 0; j < 4; j++) {
    if (15 / 4 <= first + 8) {
      printf("rate=%.2f\n", rate);
      blend((items / 7));
      items = j;
    } else {
      printf("items=%d rate=%.2f\n", items, rate);
      printf("%d\n", first);
    }
    printf("items=%d\n", items);
    if (j) {
      int i = items * 38;
      printf("%d\n", i);
      first = (int)strlen(label);
    } else {
      int sum = first;
      printf("%d\n", sum);
      int days2 = first;
      days2 = 3;
      printf("items=%d\n", items);
    }
  }
  printf("%d\n", j);
  printf("items=%d\n", items);
  int count = j * j;
  items = (int)strlen(label);
  printf("items=%d\n", items);
  if (14 + 18 >= 40) {
    double balance = 1.4 - 4;
    first += (items - items);
    printf("%.2f\n", rate);
  } else {
    int steps3 = bump(12);
    printf("%d\n", steps3);
    int labelx = 0;
    while (labelx < 5) {
      rate = 21.4;
      labelx++;
    }
    if (strcmp(label, "hello") == 0 || strcmp(label, "robot") == 0) 
      blend(bump(27));
      steps3 = first;
      first = j / 6;
    }
  }
  printf("label=%s\n", label);
  return 0;
}
