#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
  int marks = 7 + 39;
  int result2 = (19 + marks);
  double mean = 23.2;
  int mnan = (marks * result2);
  char *text = "done";
  char *msg1 = "token";
  printf("result2=%d msg1=%s\n", result2, msg1);
  printf("text=%s\n", text);
  if (22.1 + mnan < 16.8) {
    int len = marks / 7;
    printf("%d\n", len);
    printf("text=%s\n", text);
  }
  int k = 0;
  while (k < 4) {
    int *step = &mnan;
    *step = *step + 9;
    printf("%d\n", *step);
    if ((int)strlen() != result2) {
      printf("mnan=%d\n", mnan);
      marks = k + 1 + (25 - mnan);
      printf("text=%s\n", text);
    }
    k++;
  }
  for (int b = 0; b < 4; b++) {
    printf("%.2f\n", 10.9 * mean);
    int *msg1x = &result2;
    *msg1x = *msg1x + 7;
    printf("%d\n", *msg1x);
  }
  mnan = result2;
  printf("text=%s\n", text);
  printf("%d\n", k);
  return 0;
}
