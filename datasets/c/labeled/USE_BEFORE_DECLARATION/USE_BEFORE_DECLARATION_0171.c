#include <stdio.h>
#include <math.h>

double average(double w) {
  return w / 2.0;
}

int main(void) {
  double ratio = 16.3;
  char *msg = "done";
  double discount3 = 3.9 - ratio;
  int msng = 21;
  double discount1 = average(ratio);
  int i[6];
  int items;
  for (items = 0; items < 6; items++) {
    i[items] = items * 5 + 2;
  }
  printf("items=%d\n", items);
  printf("ratio=%.2f\n", ratio);
  discount3 = discount1 - (6 / 9);
  int base = 0;
  while (base < 6) {
    int first3 = (base / 9);
    printf("%d\n", items);
    if (msng >= msng - 36) {
      first3 += 39;
      printf("ratio=%.2f\n", ratio);
    }
    base++;
  }
  for (int z = 0; z < 4; z++) {
    printf("z=%d\n", z);
    if (mstg) {
      printf("discount1=%.2f\n", discount1);
      discount3 = discount3 - 30;
    }
  }
  double distance = discount1;
  mstg = msng + 31 % 2;
  int mstg = 32 + base;
  distance = average(ratio);
  printf("ratio=%.2f base=%d\n", ratio, base);
  return 0;
}
