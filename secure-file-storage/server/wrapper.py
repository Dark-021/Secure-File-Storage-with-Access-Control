# wrapper.py - loads bloom.dll and trie.dll and exposes simple Python API
import ctypes, os
from ctypes import c_void_p, c_char_p, c_size_t, c_int

HERE = os.path.dirname(__file__)
DLL_DIR = os.path.join(HERE, '..', 'csrc')

bloom = ctypes.CDLL(os.path.join(DLL_DIR, 'bloom.dll'))
trie = ctypes.CDLL(os.path.join(DLL_DIR, 'trie.dll'))

# Bloom signatures
bloom.bf_create.restype = c_void_p
bloom.bf_create.argtypes = [c_size_t]
bloom.bf_add.restype = None
bloom.bf_add.argtypes = [c_void_p, c_char_p, c_size_t, c_int]
bloom.bf_check.restype = c_int
bloom.bf_check.argtypes = [c_void_p, c_char_p, c_size_t, c_int]
bloom.bf_free.restype = None
bloom.bf_free.argtypes = [c_void_p]

# Trie signatures
trie.trie_create.restype = c_void_p
trie.trie_create.argtypes = []
trie.trie_insert.restype = None
trie.trie_insert.argtypes = [c_void_p, c_char_p]
trie.trie_search_exact.restype = c_int
trie.trie_search_exact.argtypes = [c_void_p, c_char_p]
trie.trie_has_prefix.restype = c_int
trie.trie_has_prefix.argtypes = [c_void_p, c_char_p]
trie.trie_free.restype = None
trie.trie_free.argtypes = [c_void_p]

class Bloom:
    def __init__(self, m_bits=65536, k=6):
        self.m = m_bits
        self.k = k
        self.ptr = bloom.bf_create(self.m)
    def add(self, s: str):
        bloom.bf_add(self.ptr, s.encode('utf-8'), self.m, self.k)
    def check(self, s: str) -> bool:
        return bool(bloom.bf_check(self.ptr, s.encode('utf-8'), self.m, self.k))
    def free(self):
        bloom.bf_free(self.ptr)

class Trie:
    def __init__(self):
        self.ptr = trie.trie_create()
    def insert(self, s: str):
        trie.trie_insert(self.ptr, s.encode('utf-8'))
    def search_exact(self, s: str) -> bool:
        return bool(trie.trie_search_exact(self.ptr, s.encode('utf-8')))
    def has_prefix(self, pref: str) -> bool:
        return bool(trie.trie_has_prefix(self.ptr, pref.encode('utf-8')))
    def free(self):
        trie.trie_free(self.ptr)
