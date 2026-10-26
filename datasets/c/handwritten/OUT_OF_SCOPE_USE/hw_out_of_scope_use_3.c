#include <stdio.h>

int main(void) {
    int x = 8;
    while (x > 6) {
        int step = 1;
        x -= step;
    }
    printf("%d %d\n", x, step);
    return 0;
}
