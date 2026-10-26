"""Twenty ordinary, textbook-style C programs (structs, pointers, recursion, function pointers, unions, macros, goto ...)
used as the starting point of the stress test. Every one of them is accepted by gcc; the test breaks them in many ways."""

PROGRAMS = {}

PROGRAMS["linked_list"] = r'''#include <stdio.h>
#include <stdlib.h>

struct Node {
    int value;
    struct Node *next;
};

struct Node *push(struct Node *head, int value) {
    struct Node *n = malloc(sizeof(struct Node));
    n->value = value;
    n->next = head;
    return n;
}

int sum(struct Node *head) {
    int total = 0;
    while (head != NULL) {
        total += head->value;
        head = head->next;
    }
    return total;
}

int main(void) {
    struct Node *list = NULL;
    for (int i = 1; i <= 5; i++) {
        list = push(list, i * i);
    }
    printf("sum = %d\n", sum(list));
    while (list) {
        struct Node *next = list->next;
        free(list);
        list = next;
    }
    return 0;
}
'''

PROGRAMS["matrix"] = r'''#include <stdio.h>

#define N 3

void multiply(int a[N][N], int b[N][N], int c[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            c[i][j] = 0;
            for (int k = 0; k < N; k++) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}

int main(void) {
    int a[N][N] = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
    int b[N][N] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
    int c[N][N];
    multiply(a, b, c);
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            printf("%d ", c[i][j]);
        }
        printf("\n");
    }
    return 0;
}
'''

PROGRAMS["palindrome"] = r'''#include <stdio.h>
#include <string.h>
#include <ctype.h>

int is_palindrome(const char *s) {
    int i = 0;
    int j = (int)strlen(s) - 1;
    while (i < j) {
        while (i < j && !isalnum((unsigned char)s[i])) i++;
        while (i < j && !isalnum((unsigned char)s[j])) j--;
        if (tolower((unsigned char)s[i]) != tolower((unsigned char)s[j])) {
            return 0;
        }
        i++;
        j--;
    }
    return 1;
}

int main(void) {
    const char *words[] = {"level", "A man, a plan, a canal: Panama", "compiler"};
    for (int i = 0; i < 3; i++) {
        printf("%s -> %s\n", words[i], is_palindrome(words[i]) ? "yes" : "no");
    }
    return 0;
}
'''

PROGRAMS["sieve"] = r'''#include <stdio.h>
#include <stdbool.h>

#define LIMIT 50

int main(void) {
    bool composite[LIMIT + 1] = {false};
    int count = 0;
    for (int i = 2; i <= LIMIT; i++) {
        if (!composite[i]) {
            printf("%d ", i);
            count++;
            for (int j = i * i; j <= LIMIT; j += i) {
                composite[j] = true;
            }
        }
    }
    printf("\n%d primes\n", count);
    return 0;
}
'''

PROGRAMS["sorting"] = r'''#include <stdio.h>

void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}

void selection_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int min = i;
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[min]) {
                min = j;
            }
        }
        if (min != i) {
            swap(&arr[i], &arr[min]);
        }
    }
}

int main(void) {
    int data[] = {64, 25, 12, 22, 11, 90};
    int n = sizeof(data) / sizeof(data[0]);
    selection_sort(data, n);
    for (int i = 0; i < n; i++) {
        printf("%d%s", data[i], i + 1 < n ? ", " : "\n");
    }
    return 0;
}
'''

PROGRAMS["students"] = r'''#include <stdio.h>
#include <string.h>

typedef struct {
    char name[20];
    int marks[3];
    double average;
} Student;

void compute(Student *s) {
    int total = 0;
    for (int i = 0; i < 3; i++) {
        total += s->marks[i];
    }
    s->average = total / 3.0;
}

int main(void) {
    Student class_list[2];
    strcpy(class_list[0].name, "Asha");
    strcpy(class_list[1].name, "Ravi");
    int scores[2][3] = {{90, 85, 77}, {60, 72, 88}};
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 3; j++) {
            class_list[i].marks[j] = scores[i][j];
        }
        compute(&class_list[i]);
        printf("%s: %.2f\n", class_list[i].name, class_list[i].average);
    }
    return 0;
}
'''

PROGRAMS["recursion"] = r'''#include <stdio.h>

int fib(int n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

int gcd(int a, int b) {
    return b == 0 ? a : gcd(b, a % b);
}

long power(int base, int exp) {
    if (exp == 0) return 1;
    long half = power(base, exp / 2);
    return exp % 2 ? half * half * base : half * half;
}

void hanoi(int n, char from, char to, char via) {
    if (n == 0) return;
    hanoi(n - 1, from, via, to);
    printf("move disk %d from %c to %c\n", n, from, to);
    hanoi(n - 1, via, to, from);
}

int main(void) {
    printf("fib(10) = %d\n", fib(10));
    printf("gcd(48, 18) = %d\n", gcd(48, 18));
    printf("2^10 = %ld\n", power(2, 10));
    hanoi(2, 'A', 'C', 'B');
    return 0;
}
'''

PROGRAMS["callbacks"] = r'''#include <stdio.h>
#include <stdlib.h>

typedef int (*binop)(int, int);

int add(int a, int b) { return a + b; }
int mul(int a, int b) { return a * b; }

int apply(binop f, int a, int b) {
    return f(a, b);
}

int compare(const void *x, const void *y) {
    return *(const int *)x - *(const int *)y;
}

int main(void) {
    binop ops[] = {add, mul};
    for (int i = 0; i < 2; i++) {
        printf("%d\n", apply(ops[i], 6, 7));
    }
    int values[] = {5, 3, 9, 1};
    qsort(values, 4, sizeof(int), compare);
    for (int i = 0; i < 4; i++) {
        printf("%d ", values[i]);
    }
    printf("\n");
    return 0;
}
'''

PROGRAMS["menu"] = r'''#include <stdio.h>

enum Command { START, STOP, PAUSE, QUIT };

const char *describe(enum Command c) {
    switch (c) {
        case START: return "starting";
        case STOP: return "stopping";
        case PAUSE: return "pausing";
        case QUIT: return "quitting";
        default: return "unknown";
    }
}

int main(void) {
    enum Command script[] = {START, PAUSE, START, STOP, QUIT};
    int n = sizeof(script) / sizeof(script[0]);
    for (int i = 0; i < n; i++) {
        printf("%d: %s\n", i, describe(script[i]));
        if (script[i] == QUIT) {
            break;
        }
    }
    return 0;
}
'''

PROGRAMS["bits"] = r'''#include <stdio.h>
#include <stdint.h>

#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

union Word {
    uint32_t value;
    uint8_t bytes[4];
};

int count_bits(uint32_t x) {
    int count = 0;
    while (x) {
        count += x & 1;
        x >>= 1;
    }
    return count;
}

int main(void) {
    union Word w;
    w.value = 0x12345678u;
    printf("first byte: %02x\n", (unsigned)w.bytes[0]);
    printf("bits set: %d\n", count_bits(w.value));
    printf("%d %d\n", SQUARE(7), MAX(3, 9));
    return 0;
}
'''

PROGRAMS["dynamic_array"] = r'''#include <stdio.h>
#include <stdlib.h>

int binary_search(const int *a, int n, int key) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == key) return mid;
        if (a[mid] < key) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

int main(void) {
    int capacity = 2, size = 0;
    int *data = malloc(capacity * sizeof(int));
    for (int i = 0; i < 10; i++) {
        if (size == capacity) {
            capacity *= 2;
            data = realloc(data, capacity * sizeof(int));
        }
        data[size++] = i * 3;
    }
    printf("index of 12: %d\n", binary_search(data, size, 12));
    free(data);
    return 0;
}
'''

PROGRAMS["stack"] = r'''#include <stdio.h>

#define MAX 16

typedef struct {
    int items[MAX];
    int top;
} Stack;

void init(Stack *s) { s->top = -1; }

int push(Stack *s, int v) {
    if (s->top == MAX - 1) return 0;
    s->items[++s->top] = v;
    return 1;
}

int pop(Stack *s, int *out) {
    if (s->top < 0) return 0;
    *out = s->items[s->top--];
    return 1;
}

int main(void) {
    Stack st;
    init(&st);
    for (int i = 1; i <= 4; i++) push(&st, i * 10);
    int v;
    while (pop(&st, &v)) {
        printf("%d ", v);
    }
    printf("\n");
    return 0;
}
'''

PROGRAMS["loops_goto"] = r'''#include <stdio.h>

int main(void) {
    int i = 0;
    int total = 0;
retry:
    i++;
    if (i % 2 == 0) goto retry;
    total += i;
    if (i < 9) goto retry;
    printf("odd total = %d\n", total);
    int n = 5;
    do {
        n -= 2;
        if (n == 1) continue;
        printf("n = %d\n", n);
    } while (n > 0);
    return 0;
}
'''

PROGRAMS["calculator"] = r'''#include <stdio.h>

double calculate(double a, char op, double b, int *ok) {
    *ok = 1;
    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/':
            if (b == 0) {
                *ok = 0;
                return 0;
            }
            return a / b;
        default:
            *ok = 0;
            return 0;
    }
}

int main(void) {
    const char ops[] = {'+', '-', '*', '/', '%'};
    for (int i = 0; i < 5; i++) {
        int ok;
        double r = calculate(8, ops[i], 2, &ok);
        if (ok) printf("8 %c 2 = %.1f\n", ops[i], r);
        else printf("8 %c 2 is not supported\n", ops[i]);
    }
    return 0;
}
'''

PROGRAMS["temperature"] = r'''#include <stdio.h>
#include <math.h>

double to_fahrenheit(double c) {
    return c * 9.0 / 5.0 + 32.0;
}

int main(void) {
    for (int c = -10; c <= 40; c += 10) {
        printf("%4d C = %6.1f F\n", c, to_fahrenheit(c));
    }
    double a = 3.0, b = 4.0;
    printf("hypotenuse = %.2f\n", sqrt(pow(a, 2) + pow(b, 2)));
    return 0;
}
'''

PROGRAMS["vowels"] = r'''#include <stdio.h>

int is_vowel(char c) {
    switch (c) {
        case 'a': case 'e': case 'i': case 'o': case 'u':
        case 'A': case 'E': case 'I': case 'O': case 'U':
            return 1;
    }
    return 0;
}

int main(void) {
    const char *text = "Reinforcement learning for compilers";
    int vowels = 0, words = 1;
    for (const char *p = text; *p != '\0'; p++) {
        if (is_vowel(*p)) vowels++;
        if (*p == ' ') words++;
    }
    printf("%d vowels in %d words\n", vowels, words);
    return 0;
}
'''

PROGRAMS["string_table"] = r'''#include <stdio.h>
#include <string.h>

int main(void) {
    char names[3][12] = {"alpha", "beta", "gamma"};
    char joined[64] = "";
    for (int i = 0; i < 3; i++) {
        strcat(joined, names[i]);
        if (i < 2) strcat(joined, "-");
    }
    printf("%s (%zu chars)\n", joined, strlen(joined));
    const char *days[] = {"Mon", "Tue", "Wed"};
    for (size_t i = 0; i < sizeof(days) / sizeof(days[0]); i++) {
        printf("%zu=%s ", i, days[i]);
    }
    printf("\n");
    return 0;
}
'''

PROGRAMS["counters"] = r'''#include <stdio.h>

static int calls = 0;
const int LIMIT = 3;

int next_id(void) {
    static int id = 100;
    calls++;
    return id++;
}

void report(const char *label, int value) {
    printf("%s: %d\n", label, value);
}

int main(void) {
    for (int i = 0; i < LIMIT; i++) {
        report("id", next_id());
    }
    report("calls", calls);
    return 0;
}
'''

PROGRAMS["hex_sizes"] = r'''#include <stdio.h>
#include <limits.h>

int main(void) {
    unsigned int flags = 0xA5u;
    printf("flags = 0x%X, %u\n", flags, flags << 2);
    printf("sizeof(int)=%zu sizeof(double)=%zu\n", sizeof(int), sizeof(double));
    printf("INT_MAX=%d\n", INT_MAX);
    long big = 1L << 40;
    printf("%ld\n", big);
    return 0;
}
'''

PROGRAMS["bank"] = r'''#include <stdio.h>
#include <string.h>

struct Account {
    int id;
    char owner[16];
    double balance;
};

int withdraw(struct Account *a, double amount) {
    if (amount > a->balance) {
        return 0;
    }
    a->balance -= amount;
    return 1;
}

void print_account(const struct Account *a) {
    printf("#%d %-8s %8.2f\n", a->id, a->owner, a->balance);
}

int main(void) {
    struct Account accounts[2] = {{1, "Meera", 250.0}, {2, "Dev", 40.5}};
    withdraw(&accounts[0], 100);
    if (!withdraw(&accounts[1], 100)) {
        printf("insufficient funds for %s\n", accounts[1].owner);
    }
    for (int i = 0; i < 2; i++) print_account(&accounts[i]);
    return 0;
}
'''

PROGRAMS["queue_ring"] = r'''#include <stdio.h>

#define SIZE 4

int main(void) {
    int buffer[SIZE];
    int head = 0, tail = 0, count = 0;
    for (int v = 1; v <= 6; v++) {
        if (count == SIZE) {
            head = (head + 1) % SIZE;
            count--;
        }
        buffer[tail] = v;
        tail = (tail + 1) % SIZE;
        count++;
    }
    for (int i = 0; i < count; i++) {
        printf("%d ", buffer[(head + i) % SIZE]);
    }
    printf("\n");
    return 0;
}
'''
