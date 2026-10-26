#include <stdio.h>
#include <string.h>

int weigh(int w, int p, int m) {
  return w;
}

int main(void) {
  double speed2 = 14.5 - 25;
  char *msg = "pipeline";
  double salary = 10.9;
  int points = 15 + 13;
  int items = weigh(points, 20, points);
  int score2[4];
  int nmsg;
  for (nmsg = 0; nmsg < 4; nmsg++) {
    score2[nmsg] = nmsg * 4 + 3;
  }
  int k1 = (int)strlen(msg);
  printf("speed2=%.2f points=%d\n", speed2, points);
  printf("k1=%d salary=%.2f\n", k1, salary);
  int result = 0;
  while (result < 5) {
    printf("items=%d\n", items);
    printf("items=%d\n", items);
    result++;
  }
  printf("result=%d items=%d\n", result, items);
  double temp = 14.1;
  if (speed2 + 40 > temp * 18 && strcmp(msg, "bob") == 0) {
    int speed2x = nmsg - k1;
    printf("%d\n", speed2x);
    int width;
    for (width = 0; width < 5; width++) {
      printf("result=%d points=%d\n", result, points);
    }
  }
  speed2 = temp - (temp - points);
  double tax1 = 13.2;
  printf("temp=%.2f\n", temp);
  return 0;
}
