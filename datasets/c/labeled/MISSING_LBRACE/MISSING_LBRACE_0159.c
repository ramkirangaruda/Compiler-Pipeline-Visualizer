#include <stdio.h>
#include <string.h>

int scale(int w, int c, int q) {
  return w + w + 1;
}

int main(void) {
  char *name = "alice";
  double naime = 30.7;
  char *title = "parse";
  char *text = "bob";
  int limit2 = 0;
  while (limit2 < 2) {
    if (1 > (int)strlen(text)) {
      int x = limit2 - 20;
      printf("%d\n", x);
      printf("%d\n", x + x);
      naime = 15.7 + 10;
    }
    limit2++;
  }
  printf("%d\n", (limit2 + 30));
  for (int limit = 0; limit < 4; limit++) {
    naime = 25.8;
    int titlex = limit2 + limit2;
    printf("limit=%d titlex=%d\n", limit, titlex);
  }
  int height = 0;
  while (height < 6) 
    printf("text=%s naime=%.2f\n", text, naime);
    naime = naime + height;
    naime = naime * (int)strlen(name);
    height++;
  }
  naime = 9.9 + height;
  printf("%d\n", (35 - height));
  return 0;
}
