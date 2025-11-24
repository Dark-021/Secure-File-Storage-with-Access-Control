// trie.c - basic Trie for lowercase/uppercase letters + digits + '-' '_' '.' (demo)
// Not optimized for production; simple node-based trie with insert & prefix search

#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define CHILDREN  64  // map allowed chars to indices

typedef struct TrieNode {
    struct TrieNode *children[CHILDREN];
    int is_end;
} TrieNode;

static TrieNode* new_node() {
    TrieNode *n = (TrieNode*)calloc(1, sizeof(TrieNode));
    n->is_end = 0;
    return n;
}

// map char to index (simple mapping)
static int cmap(char c) {
    if (c >= 'a' && c <= 'z') return c - 'a';
    if (c >= 'A' && c <= 'Z') return 26 + (c - 'A');
    if (c >= '0' && c <= '9') return 52 + (c - '0');
    if (c == '-') return 62;
    if (c == '_') return 63;
    // else map to 0 (rare)
    return 0;
}

__declspec(dllexport) void* trie_create() {
    return (void*)new_node();
}

__declspec(dllexport) void trie_free_node(TrieNode *node) {
    if (!node) return;
    for (int i=0;i<CHILDREN;i++) if (node->children[i]) trie_free_node(node->children[i]);
    free(node);
}
__declspec(dllexport) void trie_free(void *t) { trie_free_node((TrieNode*)t); }

__declspec(dllexport) void trie_insert(void *t, const char *s) {
    TrieNode *node = (TrieNode*)t;
    while (*s) {
        int idx = cmap(*s);
        if (!node->children[idx]) node->children[idx] = new_node();
        node = node->children[idx];
        s++;
    }
    node->is_end = 1;
}

__declspec(dllexport) int trie_search_exact(void *t, const char *s) {
    TrieNode *node = (TrieNode*)t;
    while (*s) {
        int idx = cmap(*s);
        if (!node->children[idx]) return 0;
        node = node->children[idx];
        s++;
    }
    return node->is_end;
}

// prefix search: return number of completions up to limit.
// We'll return count and optionally fill a provided buffer with up to 'limit' results,
// but to keep C<->Python simple, we'll implement a simple existence check for a prefix:
// return 1 if any word starts with prefix, else 0
__declspec(dllexport) int trie_has_prefix(void *t, const char *pref) {
    TrieNode *node = (TrieNode*)t;
    while (*pref) {
        int idx = cmap(*pref);
        if (!node->children[idx]) return 0;
        node = node->children[idx];
        pref++;
    }
    // if we reached here, at least one node exists under this prefix
    return 1;
}
