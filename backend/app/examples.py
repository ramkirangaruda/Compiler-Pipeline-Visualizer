"""Example programs shown in the Studio: working programs that showcase the
pipeline, and one broken program per error cause that showcases the ML repair."""

VALID = [
    ("sum", "Sum 1..N", "Loops, accumulators and constant folding.",
     """int n = 10;
int sum = 0;
int i = 1;
while (i <= n) {
  sum = sum + i;
  i = i + 1;
}
print(sum);
"""),
    ("factorial", "Factorial", "Multiplicative loop with a bool flag.",
     """int n = 6;
int fact = 1;
int i = 1;
while (i <= n) {
  fact = fact * i;
  i = i + 1;
}
print(fact);
bool big = fact > 500;
print(big);
"""),
    ("gcd", "GCD (Euclid)", "Nested control flow: while + if/else.",
     """int a = 48;
int b = 18;
while (a != b) {
  if (a > b) {
    a = a - b;
  } else {
    b = b - a;
  }
}
print(a);
"""),
    ("fibonacci", "Fibonacci", "Several live variables across loop iterations.",
     """int prev = 0;
int curr = 1;
int count = 0;
while (count < 10) {
  print(prev);
  int next = prev + curr;
  prev = curr;
  curr = next;
  count = count + 1;
}
"""),
    ("optimizer", "Optimizer showcase", "Constant folding, copy propagation, dead stores and branch folding.",
     """int base = 4 * 5;
int unused = base * 100;
int copy = base;
int answer = copy + 2 * 3;
if (true) {
  print(answer);
} else {
  print(0);
}
int x = answer * 1 + 0;
print(x);
"""),
    ("types", "Typed expressions", "Floats, strings, booleans and short-circuit evaluation.",
     """float price = 19.99;
int qty = 3;
float total = price * qty;
string label = "total=";
bool cheap = total < 100.0 && qty > 1;
print(label + "ok");
print(total);
print(cheap);
if (cheap || qty == 0) {
  print("discount applies");
}
"""),
]

# label, id, title, program
BROKEN = [
    ("MISSING_SEMICOLON", "Missing semicolon",
     """int width = 10;
int height = 20
int area = width * height;
print(area);
"""),
    ("MISSING_RPAREN", "Missing closing parenthesis",
     """int score = 72;
if (score > 50 {
  print("pass");
}
"""),
    ("MISSING_LPAREN", "Missing opening parenthesis",
     """int speed = 80;
if speed > 60) {
  print("slow down");
}
"""),
    ("MISSING_RBRACE", "Missing closing brace",
     """int lives = 3;
while (lives > 0) {
  print(lives);
  lives = lives - 1;
print("game over");
"""),
    ("MISSING_LBRACE", "Missing opening brace",
     """int i = 0;
while (i < 3)
  print(i);
  i = i + 1;
}
"""),
    ("MISSPELLED_KEYWORD", "Misspelled keyword",
     """int count = 3;
whlie (count > 0) {
  count = count - 1;
}
print(count);
"""),
    ("ASSIGN_EQ_CONFUSION", "= instead of ==",
     """int level = 2;
if (level = 2) {
  print("level two");
}
"""),
    ("TYPO_IDENTIFIER", "Misspelled variable",
     """string name = "John";
int age = 20;
print(nam);
print(age);
"""),
    ("MISSING_DECLARATION", "Missing declaration",
     """int age = 20;

name = "John";
print(name);
"""),
    ("USE_BEFORE_DECLARATION", "Use before declaration",
     """float rate = 0.5;
float cost = base * rate;
float base = 120.0;
print(cost);
"""),
    ("OUT_OF_SCOPE_USE", "Used outside its scope",
     """int n = 5;
if (n > 2) {
  int bonus = 10;
  print(bonus);
}
print(bonus);
"""),
    ("TYPE_MISMATCH", "Type mismatch",
     """float pi = 3.14;
int rounded = pi;
print(rounded);
"""),
]

MULTI = ("MULTI", "Several errors at once",
         """int total = 0;
int count = 4;
string note = 5;
total = totl + count;
print(avg);
""")


def all_examples() -> list[dict]:
    out = [
        {"id": i, "name": n, "category": "valid", "description": d, "source": s, "expected": None}
        for i, n, d, s in VALID
    ]
    for label, title, src in BROKEN:
        out.append({"id": label.lower(), "name": title, "category": "broken", "description": "", "source": src, "expected": label})
    out.append({"id": "multi", "name": MULTI[1], "category": "broken", "description": "Three independent semantic errors.",
                "source": MULTI[2], "expected": None})
    return out
