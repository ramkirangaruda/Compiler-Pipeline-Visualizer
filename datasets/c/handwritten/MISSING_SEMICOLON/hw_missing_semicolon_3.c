#include <stdio.h>

int main(void) {
    int nums[4] = {4, 8, 15, 16};
    int total = 0;
    for (int i = 0; i < 4; i++) {
        total += nums[i]
    }
    printf("sum = %d\n", total);
    return 0;
}
