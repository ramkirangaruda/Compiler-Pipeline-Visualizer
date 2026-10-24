#include <stdio.h>
#include <string.h>

int main(void) {
  int result = 33 + 2;
  int level = (result + 38);
  double speed = 2.7 * level;
  int z = level;
  int score1 = result / 3;
  double speed2 = speed * level;
  char *owner = "alice";
  for (int limit = 0; limit < 6; limit++) {
    if (speed + result >= speed2) {
      int speed2s = limit;
      printf("%d\n", speed2s);
      double discount = 0.1;
      int idx = (3 % 7);
      printf("discount=%.2f\n", discount);
    } else {
      int sum = (int)strlen(owner);
      printf("%d\n", sum);
      double salary = speed + 13.8;
      int count = (level + score1);
    }
    printf("owner=%s z=%d\n", owner, z[0]);
    printf("%.2f\n", speed2 + speed);
  }
  printf("z=%d\n", z);
  for (int steps = 0; steps < 6; steps++) {
    printf("owner=%s\n", owner);
    printf("score1=%d\n", score1);
  }
  printf("speed=%.2f\n", speed);
  char *course = "compiler";
  for (int b1 = 0; b1 < 3; b1++) {
    if ((int)strlen(course) > b1 && strcmp(owner, "alice") == 0) {
      printf("speed=%.2f\n", speed);
      int *days = &score1;
      *days = *days + 6;
      printf("%d\n", *days);
      int speedx = z;
    }
    z = (z % 9) / 6;
  }
  printf("speed=%.2f\n", speed);
  return 0;
}
