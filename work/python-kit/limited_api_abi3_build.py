import importlib.util
import sys
import sysconfig
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

c_source = r"""
#include <Python.h>
#include <limits.h>
static PyObject *total_with_fee(PyObject *self, PyObject *args) {
    long amount;
    if (!PyArg_ParseTuple(args, "l", &amount)) return NULL;
    if (amount < 0 || amount > LONG_MAX - 7) {
        PyErr_SetString(PyExc_ValueError, "amount outside contract");
        return NULL;
    }
    return PyLong_FromLong(amount + 7);
}
static PyMethodDef methods[] = {
    {"total_with_fee", total_with_fee, METH_VARARGS, "Add a fee."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "fee_native", NULL, -1, methods
};
PyMODINIT_FUNC PyInit_fee_native(void) {
    return PyModule_Create(&module);
}
"""
with TemporaryDirectory() as directory:
    source = Path(directory) / "fee_native.c"
    binary = Path(directory) / "fee_native.abi3.so"
    source.write_text(c_source, encoding="utf-8")
    command = ["cc"]
    if sys.platform == "darwin":
        command += ["-bundle", "-undefined", "dynamic_lookup"]
    elif sys.platform.startswith("linux"):
        command += ["-shared", "-fPIC"]
    else:
        raise RuntimeError("this fixture needs a POSIX compiler")
    command += ["-DPy_LIMITED_API=0x030B0000", "-I" + sysconfig.get_path("include"),
                str(source), "-o", str(binary)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    specification = importlib.util.spec_from_file_location("fee_native", binary)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    print("total", module.total_with_fee(47))
    try:
        module.total_with_fee(-1)
    except ValueError:
        print("negative_rejected", True)
