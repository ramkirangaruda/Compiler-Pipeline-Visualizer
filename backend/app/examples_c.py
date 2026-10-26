"""Example C programs for the Studio: working programs, and one broken program per error cause."""

VALID = [
    ("c_hello", "Hello, loop", "printf, a for loop and an accumulator.",
     """#include <stdio.h>

int main(void) {
    int sum = 0;
    for (int i = 1; i <= 5; i++) {
        sum += i;
        printf("i=%d sum=%d\\n", i, sum);
    }
    return 0;
}
"""),
    ("c_factorial", "Recursive factorial", "A function calling itself.",
     """#include <stdio.h>

int factorial(int n) {
    if (n <= 1)
        return 1;
    return n * factorial(n - 1);
}

int main(void) {
    for (int i = 1; i <= 8; i++)
        printf("%d! = %d\\n", i, factorial(i));
    return 0;
}
"""),
    ("c_primes", "Primes below 30", "Nested loops, break and a helper function.",
     """#include <stdio.h>

int is_prime(int n) {
    if (n < 2) return 0;
    for (int d = 2; d * d <= n; d++) {
        if (n % d == 0) return 0;
    }
    return 1;
}

int main(void) {
    for (int n = 2; n < 30; n++) {
        if (is_prime(n))
            printf("%d ", n);
    }
    printf("\\n");
    return 0;
}
"""),
    ("c_sort", "Bubble sort", "Arrays and swapping.",
     """#include <stdio.h>

int main(void) {
    int a[6] = {5, 2, 9, 1, 7, 3};
    for (int i = 0; i < 6; i++) {
        for (int j = 0; j < 5 - i; j++) {
            if (a[j] > a[j + 1]) {
                int t = a[j];
                a[j] = a[j + 1];
                a[j + 1] = t;
            }
        }
    }
    for (int i = 0; i < 6; i++)
        printf("%d ", a[i]);
    printf("\\n");
    return 0;
}
"""),
    ("c_pointers", "Pointers and strings", "Pointer arithmetic over a string and a swap through pointers.",
     """#include <stdio.h>
#include <string.h>

void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}

int main(void) {
    int x = 3, y = 8;
    swap(&x, &y);
    printf("x=%d y=%d\\n", x, y);

    char *word = "compiler";
    int vowels = 0;
    for (char *p = word; *p; p++) {
        if (*p == 'a' || *p == 'e' || *p == 'i' || *p == 'o' || *p == 'u')
            vowels++;
    }
    printf("%s has %d vowels in %d letters\\n", word, vowels, (int)strlen(word));
    return 0;
}
"""),
    ("c_struct", "Structs", "A struct, a pointer to it and a function that updates it.",
     """#include <stdio.h>

struct Point {
    int x;
    int y;
};

void move(struct Point *p, int dx, int dy) {
    p->x += dx;
    p->y += dy;
}

int main(void) {
    struct Point p;
    p.x = 1;
    p.y = 2;
    move(&p, 10, 20);
    printf("(%d, %d)\\n", p.x, p.y);
    return 0;
}
"""),
]

BROKEN = [
    ("MISSING_SEMICOLON", "Missing semicolon",
     """#include <stdio.h>

int main(void) {
    int a = 5
    int b = 7;
    printf("%d\\n", a + b);
    return 0;
}
"""),
    ("MISSING_RPAREN", "Missing closing parenthesis",
     """#include <stdio.h>

int main(void) {
    int a = 5;
    if ((a + 2) > 6 {
        printf("big\\n");
    }
    return 0;
}
"""),
    ("MISSING_LPAREN", "Missing opening parenthesis",
     """#include <stdio.h>

int main(void) {
    int n = 12;
    if n % 2 == 0) {
        printf("even\\n");
    }
    return 0;
}
"""),
    ("MISSING_RBRACE", "Missing closing brace",
     """#include <stdio.h>

int main(void) {
    for (int i = 0; i < 3; i++) {
        printf("%d\\n", i);
    return 0;
}
"""),
    ("MISSING_LBRACE", "Missing opening brace",
     """#include <stdio.h>

int main(void) {
    int n = 5;
    if (n > 3)
        printf("a\\n");
        printf("b\\n");
    }
    return 0;
}
"""),
    ("MISSPELLED_KEYWORD", "Misspelled keyword",
     """#include <stdio.h>

int main(void) {
    itn total = 10;
    printf("%d\\n", total);
    return 0;
}
"""),
    ("ASSIGN_EQ_CONFUSION", "'=' and '==' confused",
     """#include <stdio.h>

int main(void) {
    int limit == 10;
    printf("%d\\n", limit);
    return 0;
}
"""),
    ("TYPO_IDENTIFIER", "Misspelled variable",
     """#include <stdio.h>

int main(void) {
    int counter = 0;
    counter++;
    printf("%d\\n", conter);
    return 0;
}
"""),
    ("MISSING_DECLARATION", "Missing declaration",
     """#include <stdio.h>

int main(void) {
    int a = 4;
    int b = 6;
    sum = a + b;
    printf("%d\\n", sum);
    return 0;
}
"""),
    ("USE_BEFORE_DECLARATION", "Used before declaration",
     """#include <stdio.h>

int main(void) {
    printf("%d\\n", result);
    int result = 42;
    return 0;
}
"""),
    ("OUT_OF_SCOPE_USE", "Used outside its scope",
     """#include <stdio.h>

int main(void) {
    for (int i = 0; i < 4; i++) {
        printf("%d\\n", i);
    }
    printf("last = %d\\n", i);
    return 0;
}
"""),
    ("TYPE_MISMATCH", "Type mismatch",
     """#include <stdio.h>

int main(void) {
    int age = "twenty";
    printf("%d\\n", age);
    return 0;
}
"""),
    ("MISSING_INCLUDE", "Missing #include",
     """int main(void) {
    double r = sqrt(16.0);
    printf("%.1f\\n", r);
    return 0;
}
"""),
    ("WRONG_ARG_COUNT", "Wrong number of arguments",
     """#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main(void) {
    printf("%d\\n", add(5));
    return 0;
}
"""),
]

MULTI = ("c_multi", "Several errors at once", """#include <stdio.h>

int twice(int x) { return 2 * x; }

int main(void) {
    int total = 0;
    for (int i = 0; i < 3; i++) {
        totl += twice(i);
    }
    printf("%d\\n", total, twice(1, 2));
    return 0;
}
""")


def c_examples() -> list[dict]:
    out = [
        {"id": i, "name": n, "category": "valid", "description": d, "source": s, "expected": None, "language": "c"}
        for i, n, d, s in VALID
    ]
    for label, title, src in BROKEN:
        out.append({"id": "c_" + label.lower(), "name": title, "category": "broken", "description": "", "source": src,
                    "expected": label, "language": "c"})
    out.append({"id": MULTI[0], "name": MULTI[1], "category": "broken", "description": "Several independent errors.",
                "source": MULTI[2], "expected": None, "language": "c"})
    return out
