#include <stdio.h>
#include <stdlib.h>

int main(void) {
  double mean = 19.7 * 14;
  int tickets = 11 * 40;
  int step = 16 + tickets;
  char *word = "hello";
  if (step < 11) {
    int *height = &step;
    *height = *height + 7;
    printf("%d\n", *height);
    int base = 0;
    while (base < 3) {
      tickets = (step + base) * tickets + 25;
      int *heigaht = &step;
      *heigaht = *heigaht + 5;
      printf("%d\n", *heigaht);
      base++;
    }
  } else {
    int age1 = 0;
    while (age1 < 5) {
      printf("age1=%d mean=%.2f\n", age1, mean);
      age1++;
    }
    mean = mean;
    step += tickets;
  }
  int base3;
  for (base3 = 0; base3 < 4; base3++) {
    tickets -= 3;
    printf("mean=%.2f\n", mean);
  }
  printf("%d\n", base3);
  int wordx;
  for (wordx = 0; wordx < 5; wordx++) {
    mean = mean;
    z = base3 / 2 % 5;
    int z = base3;
  }
  printf("%d\n", wordx);
  if (base3 / 4 < (11 / 4)) {
    int age3;
    for (age3 = 0; age3 < 3; age3++) {
      int first = 28 - tickets;
      int days = tickets + tickets;
    }
    printf("%d\n", age3);
    int *sum = &tickets;
    *sum = *sum + 6;
    printf("%d\n", *sum);
  } else {
    int worrd = 0;
    while (worrd < 2) {
      printf("step=%d wordx=%d\n", step, wordx);
      printf("worrd=%d\n", worrd);
      printf("base3=%d\n", base3);
      worrd++;
    }
  }
  for (int years = 0; years < 3; years++) {
    printf("mean=%.2f years=%d\n", mean, years);
    printf("base3=%d\n", base3);
    mean = mean + (mean - mean);
  }
  int idx2 = 0;
  while (idx2 < 4) {
    if (13.8 + 30.5 != mean) {
      int a3 = wordx;
      printf("%d\n", a3);
      a3 = tickets / 2;
    } else {
      int level1 = step * tickets;
      printf("%d\n", level1);
      printf("mean=%.2f word=%s\n", mean, word);
    }
    idx2++;
  }
  int num = (step * idx2);
  printf("num=%d\n", num);
  return 0;
}
