/*
* Copyright (C) 2009,2010 Junta de Andalucia
* 
* Authors:
*   Roberto Majadas <roberto.majadas at openshine.com>
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2, or (at your option)
* any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program; if not, write to the Free Software
* Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
* USA
*/

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

