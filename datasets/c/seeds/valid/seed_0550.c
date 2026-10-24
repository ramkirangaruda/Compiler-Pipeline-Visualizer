#include <stdio.h>
#include <string.h>

int main(void) {
  double price2 = 11.4 - 25.2;
  double distance = price2;
  char *name = "parse";
  int lives = (int)strlen(name);
  if (strcmp(name, "pipeline") == 0 || strcmp(name, "alice") == 0) {
    printf("distance=%.2f\n", distance);
    printf("lives=%d\n", lives);
  }
  int years = 19 + 19;
  if (lives * years > 16) {
    int num = 13 + 18;
    printf("%d\n", num);
    years = lives;
    price2 = 7.1 + (price2 - price2);
  }
  distance = price2 * (int)strlen(name);
  distance = distance * (19.2 + years);
  distance = 11.6 * 27;
  int points = (int)strlen(name);
  printf("distance=%.2f years=%d\n", distance, years);
  return 0;
}
