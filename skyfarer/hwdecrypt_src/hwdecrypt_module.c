#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>

#include <stdint.h>
#include <stdlib.h>

struct hwd_keyset {
    uint32_t k1;
    uint32_t k2;
    uint32_t k3;
};

typedef struct {
    PyObject_HEAD
    struct hwd_keyset pk;
} hwd_keyset_t;

static int keyset_init(hwd_keyset_t *self, PyObject *args, PyObject *kwds);
static PyObject *decrypt_buffer(PyObject *self, PyObject *args);

static PyMemberDef HWDKeysetTypeMembers[] = {
    {"key1", T_UINT, offsetof(hwd_keyset_t, pk.k1), 0, "key1"},
    {"key2", T_UINT, offsetof(hwd_keyset_t, pk.k2), 0, "key2"},
    {"key3", T_UINT, offsetof(hwd_keyset_t, pk.k3), 0, "key3"},
    {NULL} /* Sentinel */
};

static PyTypeObject HWDKeysetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "hwdecrypt.Keyset",
    .tp_doc = "Contains the RNG state for the stream cipher.",
    .tp_basicsize = sizeof(hwd_keyset_t),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc)keyset_init,
    .tp_members = HWDKeysetTypeMembers,
};

static PyMethodDef HWDTopLevel[] = {
    {"decrypt", decrypt_buffer, METH_VARARGS, "Decrypt the data within a buffer object."},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef modinfo = {
    PyModuleDef_HEAD_INIT,
    .m_name = "hwdecrypt",
    .m_doc = "C extension module for decrypting ICE data.",
    .m_size = -1,
    .m_methods = HWDTopLevel,
};

#define hwd_K3_DEFAULT 0x3039
void hwd_decrypt_buf(struct hwd_keyset *initp, uint8_t *buf, int size);

////////////////////////////////////////////////////////

static int keyset_init(hwd_keyset_t *self, PyObject *args, PyObject *kwds) {
    unsigned long k1l, k2l, k3l = hwd_K3_DEFAULT;

    if (!PyArg_ParseTuple(args, "kk|k", &k1l, &k2l, &k3l)) {
        return -1;
    }

    self->pk.k1 = (uint32_t)k1l;
    self->pk.k2 = (uint32_t)k2l;
    self->pk.k3 = (uint32_t)k3l;

    return 0;
}

static PyObject *decrypt_buffer(PyObject *self, PyObject *args) {
    hwd_keyset_t *keyset;
    Py_buffer edata;
    if (!PyArg_ParseTuple(args, "O!w*", &HWDKeysetType, &keyset, &edata)) {
        return NULL;
    }

    if (edata.len > INT_MAX || edata.len < 0) {
        PyErr_SetString(PyExc_ValueError, "invalid size");
        PyBuffer_Release(&edata);
        return NULL;
    }

    hwd_decrypt_buf(&keyset->pk, edata.buf, edata.len);
    PyBuffer_Release(&edata);

    Py_RETURN_NONE;
}

PyMODINIT_FUNC PyInit_hwdecrypt(void) {
    PyObject *m;
    if (PyType_Ready(&HWDKeysetType) < 0)
        return NULL;

    m = PyModule_Create(&modinfo);
    if (m == NULL)
        return NULL;

    Py_INCREF(&HWDKeysetType);
    if (PyModule_AddObject(m, "Keyset", (PyObject *)&HWDKeysetType) < 0) {
        Py_DECREF(&HWDKeysetType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}