import importlib.util
import sys
import sysconfig
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

c_source = r"""
#include <Python.h>
#include <limits.h>
static PyObject *score_receipt(PyObject *self, PyObject *args) {
    long amount;
    if (!PyArg_ParseTuple(args, "l", &amount)) return NULL;
    if (amount < 0 || amount > LONG_MAX / 2) {
        PyErr_SetString(PyExc_ValueError, "amount outside contract");
        return NULL;
    }
    return PyLong_FromLong(amount * 2);
}
static PyMethodDef methods[] = {
    {"score", score_receipt, METH_VARARGS, "Score a receipt."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "receipt_native", NULL, -1, methods
};
PyMODINIT_FUNC PyInit_receipt_native(void) {
    return PyModule_Create(&module);
}
"""
with TemporaryDirectory() as directory:
    source = Path(directory) / "receipt_native.c"
    binary = Path(directory) / ("receipt_native" + sysconfig.get_config_var("EXT_SUFFIX"))
    source.write_text(c_source, encoding="utf-8")
    command = ["cc"]
    if sys.platform == "darwin":
        command += ["-bundle", "-undefined", "dynamic_lookup"]
    elif sys.platform.startswith("linux"):
        command += ["-shared", "-fPIC"]
    else:
        raise RuntimeError("this fixture needs a POSIX compiler")
    command += ["-I" + sysconfig.get_path("include"), str(source), "-o", str(binary)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    specification = importlib.util.spec_from_file_location("receipt_native", binary)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    print("score", module.score(47))
    try:
        module.score("47")
    except TypeError:
        print("text_rejected", True)
