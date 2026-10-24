#include <stdio.h>
#include <string.h>

int main(void) {
  int second = (29 + 8);
  char *title = "robot";
  double ratio1 = 10.1 - 27.8;
  int ratiio1 = (second % 7);
  double avg = 7.1;
  int result = (8 - 6);
  int count = 0;
  while (count < 3) {
    avg = ratio1 + (avg * ratio1);
    avg = avg * (int)strlen(title);
    printf("count=%d\n", count);
    count++;
  }
  printf("ratiio1=%d avg=%.2f\n", ratiio1, avg);
  int first = 0;
  while (first < 4) {
    printf("first=%d ratiio1=%d\n", first, ratiio1);
    first++;
  }
  printf("second=%d\n", second);
  printf("%.2f\n", avg * ratiio1);
  if (avg - 2.7 != avg) {
    if (strcmp(title, "alice") == 0) {
      printf("count=%d\n", count);
    }
  } else {
    printf("ratiio1=%d\n", ratiio1);
  }
  if (strcmp(title, "compiler") == 0 && ratio1 * ratio1 > ratio1 * avg) {
    int ratii1;
    for (ratii1 = 0; ratii1 < 3; ratii1++) {
      printf("ratiio1=%d\n", ratiio1);
      printf("%d\n", ratiio1 / 3);
      printf("first=%d\n", first);
    }
  }
  if (avg + result < 26.6) {
    int days1 = (first + second);
    printf("%d\n", days1);
    second++;
    ratiio1 = (int)strlen(title);
  }
  if (strcmp(title, "compiler") == 0 && (int)strlen(title) < first) {
    printf("result=%d avg=%.2f\n", result, avg);
  }
  printf("second=%d ratiio1=%d\n", second, ratiio1);
  return 0;
}
