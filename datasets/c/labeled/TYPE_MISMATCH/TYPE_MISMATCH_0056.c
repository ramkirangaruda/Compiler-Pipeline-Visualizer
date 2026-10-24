#include <stdio.h>
#include <math.h>
#include <string.h>

void combine(int q, int m, int p) {
  printf("q=%d\n", q);
}

void mix(int b) {
  printf("b=%d\n", b);
}

int main(void) {
  int tickets = 19;
  int steps = 27 + tickets;
  int j = (tickets + tickets);
  char *name = "ok";
  int result[6];
  int nnme;
  for (nnme = 0; nnme < 6; nnme++) {
    result[nnme] = nnme * 4 + 0;
  }
  printf("steps=%d\n", steps);
  int *total = &steps;
  *total = *total + 8;
  printf("%d\n", *total);
  printf("tickets=%d name=%s\n", tickets, name);
  printf("tickets=%d\n", tickets);
  double nnome = 15.5;
  printf("%.2f\n", 22.3);
  int namre = 0;
  while (namre < 4) {
    nnome = "text";
    steps = 3;
    printf("steps=%d name=%s\n", steps, name);
    namre++;
  }
  return 0;
}
