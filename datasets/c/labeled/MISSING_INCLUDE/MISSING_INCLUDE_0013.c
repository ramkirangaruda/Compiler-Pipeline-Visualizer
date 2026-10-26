
void scale(int p, int w) {
  printf("p=%d\n", p);
}

int clamp(int m, int c) {
  return m;
}

int main(void) {
  int limit = 13 - 24;
  int j = (limit / 9);
  int value = clamp(j, 37);
  printf("limit=%d\n", limit);
  j = clamp((limit % 3), (value + limit));
  if (j && (value + limit) <= 26) {
    int years = limit - j;
    printf("%d\n", years);
    printf("value=%d limit=%d\n", value, limit);
    years = clamp(value * 27, clamp(years, 31));
    int years3 = 0;
    while (years3 < 6) {
      int *sum = &value;
      *sum = *sum + 5;
      printf("%d\n", *sum);
      printf("j=%d years=%d\n", j, years);
      printf("years3=%d j=%d\n", years3, j);
      years3++;
    }
  }
  printf("%d\n", clamp(limit, 10));
  int score = 0;
  while (score < 6) {
    printf("%d\n", clamp(22, value));
    int level = j;
    score++;
  }
  for (int marks = 0; marks < 4; marks++) {
    printf("%d\n", marks * limit);
    if (3 + score != value) {
      int width1 = value;
      printf("%d\n", width1);
      limit += value + j;
      value = (score / 1) * (23 * 23);
      printf("score=%d\n", score);
    } else {
      int base = (limit / 2);
      printf("value=%d marks=%d\n", value, marks);
      printf("marks=%d limit=%d\n", marks, limit);
    }
    printf("value=%d\n", value);
  }
  printf("%d\n", 25);
  printf("value=%d score=%d\n", value, score);
  return 0;
}
