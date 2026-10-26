"""What the C standard headers provide.

A header's declarations are fed to the parser only when the program `#include`s it -
exactly like a real compiler - so using `printf` without <stdio.h> is a genuine,
diagnosable error. `HEADER_OF` maps every library name back to its header.
"""
from __future__ import annotations

import re

HEADERS: dict[str, str] = {
    "stdio.h": """
typedef struct _iobuf FILE;
extern FILE *stdin; extern FILE *stdout; extern FILE *stderr;
extern int EOF;
int printf(const char *format, ...);
int fprintf(FILE *stream, const char *format, ...);
int sprintf(char *buffer, const char *format, ...);
int snprintf(char *buffer, size_t n, const char *format, ...);
int scanf(const char *format, ...);
int sscanf(const char *str, const char *format, ...);
int fscanf(FILE *stream, const char *format, ...);
int puts(const char *s);
int fputs(const char *s, FILE *stream);
int putchar(int c);
int getchar(void);
char *fgets(char *s, int n, FILE *stream);
FILE *fopen(const char *path, const char *mode);
int fclose(FILE *stream);
""",
    "stdlib.h": """
void *malloc(size_t size);
void *calloc(size_t n, size_t size);
void *realloc(void *p, size_t size);
void free(void *p);
void exit(int status);
int abs(int x);
long labs(long x);
int rand(void);
void srand(unsigned int seed);
int atoi(const char *s);
long atol(const char *s);
double atof(const char *s);
extern int EXIT_SUCCESS; extern int EXIT_FAILURE; extern int RAND_MAX;
""",
    "string.h": """
size_t strlen(const char *s);
char *strcpy(char *dst, const char *src);
char *strncpy(char *dst, const char *src, size_t n);
char *strcat(char *dst, const char *src);
int strcmp(const char *a, const char *b);
int strncmp(const char *a, const char *b, size_t n);
char *strchr(const char *s, int c);
char *strstr(const char *a, const char *b);
void *memset(void *p, int c, size_t n);
void *memcpy(void *dst, const void *src, size_t n);
""",
    "math.h": """
double sqrt(double x); double pow(double x, double y); double sin(double x); double cos(double x);
double tan(double x); double fabs(double x); double floor(double x); double ceil(double x);
double log(double x); double log10(double x); double exp(double x); double fmod(double x, double y);
double round(double x); double atan(double x); double atan2(double y, double x);
extern double M_PI; extern double M_E;
""",
    "ctype.h": """
int isalpha(int c); int isdigit(int c); int isalnum(int c); int isspace(int c);
int isupper(int c); int islower(int c); int toupper(int c); int tolower(int c);
""",
    "stdbool.h": """
typedef _Bool bool;
extern const _Bool true; extern const _Bool false;
""",
    "stdint.h": """
typedef signed char int8_t; typedef short int16_t; typedef int int32_t; typedef long long int64_t;
typedef unsigned char uint8_t; typedef unsigned short uint16_t; typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
""",
    "limits.h": "extern int INT_MAX; extern int INT_MIN; extern int CHAR_BIT; extern long LONG_MAX; extern long LONG_MIN;\n",
    "time.h": "typedef long time_t; typedef long clock_t; time_t time(time_t *t); clock_t clock(void); extern long CLOCKS_PER_SEC;\n",
}
KNOWN_HEADERS = set(HEADERS) | {"stddef.h", "assert.h", "errno.h", "float.h", "signal.h", "setjmp.h", "locale.h"}

# declared whenever a program includes anything: needed by several headers
BASE = "typedef unsigned long size_t; extern void *NULL;\n"


def _build_header_of() -> dict[str, str]:
    out: dict[str, str] = {}
    skip = {"int", "char", "void", "double", "long"}
    for header, text in HEADERS.items():
        flat = text.replace("\n", " ")
        for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", flat):                       # functions
            if m.group(1) not in skip:
                out.setdefault(m.group(1), header)
        for m in re.finditer(r"extern\s+[\w\s\*]*?\b([A-Za-z_]\w*)\s*;", flat):     # variables / constants
            out.setdefault(m.group(1), header)
        for m in re.finditer(r"typedef\s+[\w\s\*]*?\b([A-Za-z_]\w*)\s*;", flat):    # typedef names
            out.setdefault(m.group(1), header)
    out["true"] = out["false"] = "stdbool.h"
    out.pop("NULL", None)
    return out


HEADER_OF = _build_header_of()
# type names a beginner uses without the header that provides them
HEADER_TYPES = {n for n, h in HEADER_OF.items() if n in
                {"bool", "FILE", "time_t", "clock_t", "int8_t", "int16_t", "int32_t", "int64_t",
                 "uint8_t", "uint16_t", "uint32_t", "uint64_t"}}


def build_prelude(included: set[str]) -> str:
    """Declarations the parser sees, given the headers the program includes. Ends with a #line
    directive so the user's code starts at line 1 of file 'user.c'."""
    text = BASE + "".join(HEADERS[h] for h in HEADERS if h in included)
    return text.replace("\n", " ") + '\n#line 1 "user.c"\n'
