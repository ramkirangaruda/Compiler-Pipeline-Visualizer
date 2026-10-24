#include <stdio.h>
#include <math.h>

int main(void) {
  int count = (25 + 40);
  int j = count * count;
  int count1 = (36 % 5);
  double area1 = 28.4 * 33;
  char *city = "parse";
  printf("j=%d\n", j);
  int *days = &count;
  *days = *days + 1;
  printf("%d\n", *days);
  area1 = area1 + (count + count1);
  printf("area1=%.2f\n", area1);
  int rity = 0;
  while (rity < 3) {
    int points = count;
    count = rity * count1 + (j % 8);
    rity++;
  
  printf("city=%s\n", city);
  int second;
  for (second = 0; second < 2; second++) {
    printf("%.2f\n", 20.8);
    int i = rity;
  }
  printf("%d\n", second);
  count = second;
  printf("second=%d j=%d\n", second, j);
  printf("second=%d\n", second);
  return 0;
}
