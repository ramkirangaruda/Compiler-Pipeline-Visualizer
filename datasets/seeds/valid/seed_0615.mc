int steps = 10;
int items = 15 % 8;
int size = steps;
float temp = 2.3;
int num1 = size + items;
int n = 0;
for (n = 0; n < 2; n = n + 1) {
  print(num1);
}
print(n);
print(items);
size = 11;
for (int i = 0; i < 3; i = i + 1) {
  if (items * i == (n / 2)) {
    print(n);
    temp = items;
  }
}
print(items);
