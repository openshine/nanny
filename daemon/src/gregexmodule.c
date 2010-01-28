#include <config.h>
#include <Python.h>
#include <glib.h>

static PyObject*
py_regexp(PyObject* self, PyObject* args){
        char *exp;
	char *str;

        PyArg_ParseTuple(args, "ss", &exp, &str);
        return Py_BuildValue("i", g_regex_match_simple(exp, str, 0, 0));
}


static PyMethodDef gregex_methods[] = {
        {"regexp", py_regexp, METH_VARARGS},
        {NULL, NULL}
};



DL_EXPORT(void)
initgregex(void) {
        (void) Py_InitModule("gregex", gregex_methods);
}

