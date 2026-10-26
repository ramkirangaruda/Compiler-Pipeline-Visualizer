#include <stdio.h>
#include <stdlib.h>

int main(void) {
  char *msg2 = "ok";
  char *label1 = "world";
  double salary = 1.3 - 25.3;
  double temp = 4.6 - salary;
  int years = 18 + 15;
  int labeln = years;
  printf("label1=%s\n", label1);
  printf("temp=%.2f\n", temp);
  int *count = &labeln;
  *count = *count + 8;
  printf("%d\n", *count);
  int lives = 0;
  while (lives < 5) {
    if (salary != temp) {
      int j = years * years;
      printf("%d\n", j);
      temp = temp + lives;
      printf("j=%d\n", j);
      printf("label1=%s\n", label1);
    } else {
      int *counr = &labeln;
      *counr = *counr + 1;
      printf("%d\n", *counr);
      printf("salary=%.2f labeln=%d\n", salary, labeln);
      years = (lives - 9) * 13;
    }
    lives++;
  }
  temp = temp * (2 * years);
  printf("lives=%d years=%d\n", lives, years);
  salary = 30.6;
  printf("lives=%d\n", lives);
  printf("salary=%.2f\n", salary);
  return 0;
}
