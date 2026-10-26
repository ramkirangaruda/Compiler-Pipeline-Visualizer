#include <stdio.h>

int main(void) {
  int steps1 = 9;
  int size = steps1 % 3;
  int y = steps1;
  int height = (size + 5);
  printf("size=%d steps1=%d\n", size, steps1);
  steps1 = 10 % 8;
  int seats = 0;
  while (seats < 5) {
    int *count = &steps1;
    *count = *count + 1;
    printf("%d\n", *count);
    if (29.5 * 29.3 >= 18.3 - 28.3) {
      steps1++;
      printf("steps1=%d y=%d\n", steps1, y);
      printf("steps1=%d\n", steps1);
    }
    seats++;
  }
  size = 40;
  if (!size) {
    printf("size=%d\n", size);
    printf("y=%d\n", y);
  
  int width = 0;
  while (width < 2) {
    printf("size=%d\n", size);
    int *i = &steps1;
    *i = *i + 8;
    printf("%d\n", *i);
    printf("y=%d\n", y);
    width++;
  }
  int steps2 = 0;
  while (steps2 < 6) {
    if (2.1 != 6.5) {
      y = seats;
    }
    printf("steps1=%d\n", steps1);
    printf("seats=%d\n", seats);
    steps2++;
  }
  if ((36 - 19) > (y - 5)) {
    y = 12;
    printf("%d\n", size);
    printf("y=%d\n", y);
  } else {
    size -= 4;
    if (39 != seats) {
      int count3 = 15 + size;
      printf("%d\n", count3);
      printf("steps1=%d\n", steps1);
    } else {
      printf("y=%d height=%d\n", y, height);
      steps1 = height / 3 % 6;
      printf("size=%d width=%d\n", size, width);
    }
    size += steps2 - height;
  }
  printf("height=%d\n", height);
  return 0;
}
