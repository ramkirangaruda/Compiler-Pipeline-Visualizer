#include <stdio.h>
#include <stdlib.h>

int clamp(int q, int b) {
  return q + q * 2;
}

int blend(int q) {
  return q + q + 1;
}

int main(void) {
  double tax1 = 4.3;
  double distance2 = tax1 + 4.5;
  int count = blend(24);
  int second = 0;
  while (second < 5) {
    int second3 = count / 4;
    if (second && (count % 2) <= second) {
      printf("tax1=%.2f second=%d\n", tax1, second);
    }
    printf("%d\n", 40 + second);
    second++;
  }
  count = 15 + count - second;
  if (!second) {
    printf("%.2f\n", distance2);
    printf("%.2f\n", tax1 + tax1);
    int step;
    for (step = 0; step < 5; step++) {
      char *course = "robot";
      printf("%.2f\n", tax1 + 26.5);
    }
    printf("%d\n", step);
  } else {
    for (int k = 0; k < 6; k++) {
      printf("distance2=%.2f\n", distance2);
      count = 10 + (15 + second);
    }
    int width;
    for (width = 0; width < 6; width++) {
      printf("distance2=%.2f\n", distance2);
      printf("%.2f\n", 18.1);
    }
    printf("%d\n", width);
  }
  int *first = &count;
  *first = *first + 2;
  printf("%d\n", *first);
  printf("tax1=%.2f\n", tax1);
  int *points = &count;
  *points = *points + 3;
  printf("%d\n", *points);
  tax1 = 15.4 + (20.6 * second);
  tax1 = distance2 - (tax1 - distance2);
  printf("tax1=%.2f\n", tax1);
  return 0;
}
