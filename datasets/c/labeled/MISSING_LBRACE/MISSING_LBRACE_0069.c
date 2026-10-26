#include <stdio.h>
#include <math.h>

void combine(int w, int a, int b) {
  printf("w=%d\n", w);
}

int weigh(int b, int w) {
  return b;
}

int main(void) {
  int height = (35 * 24);
  int size = (21 * 14);
  char *title = "compiler";
  int items = (40 + 29);
  int z = (height - items);
  int k[3] = {10, 16, 6};
  char *word = "bob";
  printf("z=%d\n", z);
  size = size;
  printf("word=%s\n", word);
  for (int i = 0; i < 4; i++) {
    printf("word=%s size=%d\n", word, size);
    if (k[2] <= weigh(2, 7)) {
      int j1 = z;
      printf("%d\n", j1);
      combine((28 - 31), size, (height + height));
      j1 = height + items;
      printf("height=%d\n", height);
    } else {
      int age = 23 / 7;
      printf("%d\n", age);
      printf("height=%d\n", height);
    }
  }
  printf("items=%d height=%d\n", items, height);
  size = z + 2;
  int limit = 0;
  while (limit < 3) 
    printf("%d\n", items);
    double avg = sqrt(14.6 * 15.7);
    printf("%.2f\n", avg);
    limit++;
  }
  printf("title=%s\n", title);
  return 0;
}
