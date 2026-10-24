#include <stdio.h>

int twice(int x) { return 2 * x; }

int main(void) {
    printf("%d\n", twice(3, 4));
    return 0;
}
