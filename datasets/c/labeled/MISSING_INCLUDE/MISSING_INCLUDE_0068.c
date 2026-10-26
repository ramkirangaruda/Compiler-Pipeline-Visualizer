#include <stdlib.h>

int main(void) {
  double temp = 1.3;
  char *greeting = "pipeline";
  int lives = (11 - 1);
  int size = 7;
  char *word = "done";
  int temps = size;
  printf("temps=%d greeting=%s\n", temps, greeting);
  lives = (size * 26) / 3;
  size = 36 + size / 7;
  temps -= 5;
  int score3 = 0;
  while (score3 < 6) {
    printf("score3=%d\n", score3);
    int level = 4 + lives;
    score3++;
  }
  printf("lives=%d\n", lives);
  temp = 28.7 + (temp + lives);
  int *points3 = &size;
  *points3 = *points3 + 2;
  printf("%d\n", *points3);
  return 0;
}
