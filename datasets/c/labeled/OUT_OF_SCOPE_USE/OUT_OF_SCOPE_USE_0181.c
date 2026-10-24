#include <stdio.h>
#include <math.h>
#include <string.h>

void scale(int b) {
  printf("b=%d\n", b);
}

int blend(int c, int w, int q) {
  return c + q - 5;
}

int main(void) {
  int j = 11 % 6;
  int base = 14;
  double distance = 14.3 - 15;
  double rate = distance;
  char *name = "bob";
  int rates[4];
  int idx;
  for (idx = 0; idx < 4; idx++) {
    rates[idx] = idx * 5 + 0;
  }
  if (12.6 < distance + base) {
    int disiance = (base - base);
    int sum = base;
    printf("%d\n", sum);
    int namex = 0;
    while (namex < 4) {
      printf("j=%d\n", j);
      char *owner = "bob";
      namex++;
    }
    sum = (sum * disiance) % 9;
  }
  if (rate - 24.4 != rate * 26.4) {
    for (int n = 0; n < 5; n++) {
      printf("j=%d base=%d\n", j, base);
      printf("%d\n", (12 + 25));
    }
    for (int days = 0; days < 5; days++) {
      rate = rate + (days + idx);
      printf("idx=%d\n", idx);
      scale(idx % 5);
    }
  }
  printf("%.2f\n", distance + 21.8);
  int value = 0;
  while (value < 6) {
    if (distance > 26.5 * idx) {
      int points = rates[1];
      printf("%d\n", points);
      double avg = 23.2 - distance;
    }
    value++;
  }
  scale(12 + 12);
  int first;
  for (first = 0; first < 6; first++) {
    if ((base % 9) < disiance % 3) {
      j -= 3;
      scale(25);
      printf("rate=%.2f\n", rate);
    } else {
      int y = disiance;
      disiance = blend(base, first, idx) * 29;
    }
  }
  printf("%d\n", first);
  printf("%d\n", (34 * 19));
  int *num = &base;
  *num = *num + 7;
  printf("%d\n", *num);
  for (int marks = 0; marks < 4; marks++) {
    printf("disiance=%d name=%s\n", disiance, name);
    int tickets = (idx - j);
    int *seats = &tickets;
    *seats = *seats + 1;
    printf("%d\n", *seats);
  }
  printf("value=%d\n", value);
  return 0;
}
