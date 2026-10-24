#include <stdio.h>

int max(int a, int b) {
    if (a > b) {
        return a;
    }
    return b;

int main(void) {
    printf("%d\n", max(3, 9));
    return 0;
}
