#include <stdio.h>
#include <math.h>
#include <string.h>

int main(void) {
  char *greeting = "robot";
  int greetings = 20;
  double area = 11.5 - 14.1;
  int y = greetings - 2;
  double speed2 = 9.9 * area;
  double temp2 = 7.5 + greetings;
  int *level3 = &greetings;
  *level3 = *level3 + 4;
  printf("%d\n", *level3);
  int steps;
  for (steps = 0; steps < 3; steps++) {
    if (temp2 < 9.4) {
      printf("y=%d greetings=%d\n", y, greetings);
      int total = (int)strlen(greeting);
      area = sqrt(15.6 * 18.5 * total);
    }
  }
  printf("%d\n", steps);
  for (int speerd2 = 0; speerd2 < 3; speerd2++) {
    greetings = (int)strlen(greeting);
  }
  printf("y=%d\n", y);
  int a3 = 0;
  while (a3 < 5) {
    printf("area=%.2f\n", area);
    double voltage = 30.9 - area;
    a3++;
  }
  int tickets = (int)strlen(greeting);
  printf("speed2=%.2f\n", speed2);
  return 0;

