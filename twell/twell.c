#define TWELL_IMPL
#define TWELL_BUILD_DLL
#include "../twell.h"

#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyModuleDef _twellmodule = {
    PyModuleDef_HEAD_INIT,
    "_twell",
    "Twell C library wrapper",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__twell(void) {
    return PyModule_Create(&_twellmodule);
}
