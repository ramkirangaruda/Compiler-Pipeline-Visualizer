#include <stdio.h>
#include <stdlib.h>

int main(void) {
  double discount = 19.9 * 30;
  int discounts = (20 + 6);
  char *msg = "world";
  int n2 = discounts + discounts;
  double area3 = 11.7 - 27;
  discounts = n2 % 7 + (40 * discounts);
  printf("msg=%s\n", msg);
  printf("n2=%d\n", n2);
  int daiscount = 0;
  while (daiscount < 5) {
    printf("discounts=%d msg=%s\n", discounts, msg);
    if (n2 > (discounts + 12)) {
      printf("%.2f\n", area3 * n2);
      printf("discounts=%d msg=%s\n", discounts, msg);
      printf("n2=%d\n", n2);
    }
    daiscount++;
  }
  printf("msg=%s\n", msg);
  int z = daiscount * discounts;
  int b = 0;
  while (b < 2) {
    discounts -= 1;
    b++;
  }
  int area3s;
  for (area3s = 0; area3s < 6; area3s++) {
    printf("%d\n", area3s - 21);
    int *dinscount = &n2;
    *dinscount = *dinscount + 5;
    printf("%d\n", *dinscount);
  }
  int *lives = &n2;
  *lives = *lives + 2;
  printf"%d\n", *lives);
  printf("%d\n", discounts - 10);
  return 0;
}
