"""Which standard header declares which name: used to repair "implicit declaration of function 'x'" and
"unknown type name 'x'" by adding the right #include. Names not listed here are left to the compiler's own fix-its."""
from __future__ import annotations

_H = {
    "stdio.h": "printf fprintf sprintf snprintf vprintf vfprintf vsprintf vsnprintf scanf fscanf sscanf puts fputs putchar putc fputc "
               "getchar getc fgetc gets fgets ungetc fopen fclose freopen fread fwrite fflush fseek ftell rewind fgetpos fsetpos feof ferror "
               "clearerr perror remove rename tmpfile tmpnam setbuf setvbuf FILE stdin stdout stderr EOF BUFSIZ SEEK_SET SEEK_CUR SEEK_END "
               "fpos_t getline",
    "stdlib.h": "malloc calloc realloc free exit abort atexit system getenv atoi atol atoll atof strtol strtoll strtoul strtoull strtod strtof "
                "rand srand abs labs llabs div ldiv lldiv qsort bsearch mblen EXIT_SUCCESS EXIT_FAILURE RAND_MAX div_t ldiv_t _Exit "
                "aligned_alloc",
    "string.h": "strlen strcpy strncpy strcat strncat strcmp strncmp strchr strrchr strstr strtok strspn strcspn strpbrk strerror strcoll "
                "strxfrm memcpy memmove memset memcmp memchr strdup strndup strnlen",
    "math.h": "sqrt pow sin cos tan asin acos atan atan2 sinh cosh tanh exp log log10 log2 fabs floor ceil round trunc fmod cbrt hypot "
              "fmax fmin fma ldexp frexp modf expm1 log1p lround llround nearbyint rint isnan isinf isfinite signbit copysign "
              "M_PI M_E M_SQRT2 HUGE_VAL INFINITY NAN sqrtf powf sinf cosf tanf fabsf floorf ceilf roundf",
    "ctype.h": "isalpha isdigit isalnum isspace isupper islower ispunct isprint iscntrl isgraph isxdigit toupper tolower isblank",
    "time.h": "time clock difftime mktime strftime localtime gmtime asctime ctime time_t clock_t CLOCKS_PER_SEC struct_tm nanosleep "
              "clock_gettime timespec",
    "stdbool.h": "bool true false",
    "stdint.h": "int8_t int16_t int32_t int64_t uint8_t uint16_t uint32_t uint64_t intptr_t uintptr_t intmax_t uintmax_t INT8_MAX INT16_MAX "
                "INT32_MAX INT64_MAX UINT8_MAX UINT16_MAX UINT32_MAX UINT64_MAX SIZE_MAX",
    "stddef.h": "size_t ptrdiff_t NULL offsetof wchar_t max_align_t",
    "limits.h": "INT_MAX INT_MIN UINT_MAX LONG_MAX LONG_MIN ULONG_MAX CHAR_BIT CHAR_MAX CHAR_MIN SHRT_MAX SHRT_MIN USHRT_MAX LLONG_MAX "
                "LLONG_MIN ULLONG_MAX SCHAR_MAX SCHAR_MIN UCHAR_MAX",
    "float.h": "FLT_MAX FLT_MIN DBL_MAX DBL_MIN FLT_EPSILON DBL_EPSILON DBL_DIG FLT_DIG",
    "errno.h": "errno EINVAL ENOENT ENOMEM EACCES ERANGE EDOM EEXIST EINTR",
    "assert.h": "assert static_assert",
    "signal.h": "signal raise SIGINT SIGTERM SIGSEGV SIGABRT SIGFPE SIGILL sig_atomic_t",
    "setjmp.h": "setjmp longjmp jmp_buf",
    "stdarg.h": "va_list va_start va_end va_arg va_copy",
    "locale.h": "setlocale localeconv LC_ALL",
    "unistd.h": "sleep usleep read write close getpid fork pipe dup dup2 getcwd chdir access unlink isatty sysconf",
    "fcntl.h": "open creat fcntl O_RDONLY O_WRONLY O_RDWR O_CREAT O_TRUNC O_APPEND",
    "inttypes.h": "PRId64 PRIu64 PRId32 PRIu32 PRIx64 SCNd64 imaxabs",
    "wchar.h": "wprintf wcslen wcscpy wint_t",
    "iso646.h": "and or not xor",
}

HEADER_OF: dict[str, str] = {}
for _header, _names in _H.items():
    for _n in _names.split():
        HEADER_OF.setdefault(_n, _header)
HEADER_OF.pop("struct_tm", None)
HEADER_OF.pop("timespec", None)

# the order matters little; this is the list shown to a user when a program includes nothing yet
COMMON_HEADERS = ["stdio.h", "stdlib.h", "string.h", "math.h", "ctype.h", "stdbool.h", "stdint.h", "stddef.h", "limits.h", "time.h"]
