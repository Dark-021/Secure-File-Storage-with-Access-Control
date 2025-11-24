// bloom.c - simple Bloom filter (Windows DLL)
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// simple FNV-like hash variations (for demo)
static uint64_t hash1(const char *s) {
    uint64_t h = 1469598103934665603ULL;
    while (*s) h = (h ^ (unsigned char)(*s++)) * 1099511628211ULL;
    return h;
}
static uint64_t hash2(const char *s) {
    uint64_t h = 0xcbf29ce484222325ULL;
    while (*s) h = h * 16777619 ^ (unsigned char)(*s++);
    return h;
}

__declspec(dllexport) void* bf_create(size_t bits) {
    size_t bytes = (bits + 7) / 8;
    unsigned char *arr = (unsigned char*)calloc(bytes, 1);
    return (void*)arr;
}
__declspec(dllexport) void bf_free(void *bf) { free(bf); }

static void set_bit(unsigned char *a, size_t i) { a[i/8] |= (1 << (i%8)); }
static int get_bit(unsigned char *a, size_t i) { return (a[i/8] >> (i%8)) & 1; }

__declspec(dllexport) void bf_add(void *bf, const char *s, size_t m, int k) {
    unsigned char *arr = (unsigned char*)bf;
    uint64_t h1 = hash1(s);
    uint64_t h2 = hash2(s);
    for (int i = 0; i < k; ++i) {
        uint64_t comb = h1 + (uint64_t)i * h2;
        size_t idx = comb % m;
        set_bit(arr, idx);
    }
}

__declspec(dllexport) int bf_check(void *bf, const char *s, size_t m, int k) {
    unsigned char *arr = (unsigned char*)bf;
    uint64_t h1 = hash1(s);
    uint64_t h2 = hash2(s);
    for (int i = 0; i < k; ++i) {
        uint64_t comb = h1 + (uint64_t)i * h2;
        size_t idx = comb % m;
        if (!get_bit(arr, idx)) return 0;
    }
    return 1;
}
