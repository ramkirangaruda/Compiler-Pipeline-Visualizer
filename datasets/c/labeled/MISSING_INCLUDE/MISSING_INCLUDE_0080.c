#include <string.h>

void scale(int p, int b) {
  printf("p=%d\n", p);
}

int main(void) {
  double distance = 10.4 - 23.1;
  char *msg1 = "robot";
  int value = (int)strlen(msg1);
  double valaue = distance * value;
  int size2[5] = {18, 20, 7, 17, 7};
  printf("distance=%.2f\n", distance);
  printf("msg1=%s\n", msg1);
  scale(2, value);
  printf("msg1=%s valaue=%.2f\n", msg1, valaue);
  for (int score = 0; score < 3; score++) {
    if (score / 4 > 5) {
      valaue = distance;
      distance = distance;
      valaue = distance * 24;
    } else {
      int width = value * value;
      printf("%d\n", width);
      printf("%.2f\n", valaue - value);
    }
  }
  for (int first = 0; first < 2; first++) {
    printf("%d\n", value);
    distance = 21.1 - value;
    value = 31 + value;
  }
  return 0;
}
