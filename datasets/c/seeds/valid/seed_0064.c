#include <stdio.h>

double lerp(double m) {
  return m / 2.0;
}

int main(void) {
  double speed = lerp(6.1);
  int score = 4 * 27;
  double price = speed * speed;
  score -= 1;
  printf("price=%.2f\n", price);
  int limit = (15 * 3);
  int years = 0;
  while (years < 5) {
    score = limit - years;
    limit = years - 26 % 5;
    if (years) {
      score = (7 % 8) * limit;
      printf("limit=%d\n", limit);
      double salary = price * 39;
    } else {
      int sum = (18 - 4);
      printf("%d\n", sum);
      printf("sum=%d speed=%.2f\n", sum, speed);
      printf("%d\n", (years + score));
    }
    years++;
  }
  if (price * 19.4 < lerp(7.3) || limit % 5 < 14 * 31) {
    int points = 0;
    while (points < 3) {
      printf("limit=%d speed=%.2f\n", limit, speed);
      points++;
    }
    if (years < 13 * 15 || 12.9 + speed < price * price) {
      printf("speed=%.2f\n", speed);
      printf("years=%d\n", years);
    }
  } else {
    int speei = (limit + 36);
    printf("%d\n", speei);
    if (score) {
      int items = 34 + 36;
      printf("%d\n", items);
      printf("speei=%d\n", speei);
    } else if ((17 * limit) != score + 40) {
      printf("price=%.2f\n", price);
      limit = score;
    } else {
      speei += (14 / 6);
      printf("speed=%.2f\n", speed);
      printf("limit=%d score=%d\n", limit, score);
    }
  }
  if (15 <= (16 % 9)) {
    printf("limit=%d\n", limit);
    speed = price - (limit + limit);
  } else if (years) {
    int z;
    for (z = 0; z < 2; z++) {
      printf("%.2f\n", speed * price);
      printf("limit=%d\n", limit);
      printf("z=%d price=%.2f\n", z, price);
    }
    printf("%d\n", z);
  } else {
    score -= 4;
    price = 4.9 - 40;
  }
  int *base = &limit;
  *base = *base + 8;
  printf("%d\n", *base);
  score++;
  printf("price=%.2f\n", price);
  if (limit) {
    int i = 33;
    printf("%d\n", i);
    double mean2 = 24.7;
  } else if (!limit) {
    price = speed * ((12 * 9));
  } else {
    printf("years=%d\n", years);
    printf("limit=%d score=%d\n", limit, score);
    printf("price=%.2f speed=%.2f\n", price, speed);
  }
  printf("score=%d\n", score);
  return 0;
}
