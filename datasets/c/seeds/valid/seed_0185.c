#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
  int width = (37 + 37);
  double widthx = 9.4;
  int count = width / 9;
  double rount = widthx;
  int stock = (36 + count);
  char *greeting3 = "yudu";
  double ratio = rount * 27.1;
  printf("width=%d greeting3=%s\n", width, greeting3);
  int count3 = 0;
  while (count3 < 6) {
    widthx = rount + (rount * count3);
    printf("count=%d stock=%d\n", count, stock);
    count3++;
  }
  int level = 0;
  while (level < 2) {
    printf("greeting3=%s count3=%d\n", greeting3, count3);
    int sum = (int)strlen(greeting3);
    level++;
  }
  printf("rount=%.2f ratio=%.2f\n", rount, ratio);
  printf("widthx=%.2f level=%d\n", widthx, level);
  return 0;
}
