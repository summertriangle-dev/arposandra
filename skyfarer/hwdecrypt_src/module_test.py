import _hwdecrypt

ks1 = _hwdecrypt.Keyset(0, 1, 2)
print(ks1.key1, ks1.key2, ks1.key3)

ks1 = _hwdecrypt.Keyset(0, 1)
print(ks1.key1, ks1.key2, ks1.key3)


buf = bytearray(b"123456789")
print(buf)
_hwdecrypt.decrypt(ks1, buf)
print(buf)

print(ks1.key1, ks1.key2, ks1.key3)
