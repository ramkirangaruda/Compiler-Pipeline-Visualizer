#include <stdio.h>

int main(void) {
    int v = 3;
    int *p;
    p = v;
    printf("%d\n", *p);
    return 0;
}
