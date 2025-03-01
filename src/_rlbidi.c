/*
 *	This program is free software; you can redistribute it and/or modify
 *	it under the terms of the GNU General Public License as published by
 *	the Free Software Foundation; either version 2 of the License, or
 *	(at your option) any later version.
 *
 *	This program is distributed in the hope that it will be useful,
 *	but WITHOUT ANY WARRANTY; without even the implied warranty of
 *	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *	GNU General Public License for more details.
 *
 *	You should have received a copy of the GNU General Public License
 *	along with this program; if not, write to the Free Software
 *	Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

/* Copyright (C) 2005,2006,2010 Yaacov Zamir, Nir Soffer */
/* This version modified by Robin Becker */

#include <Python.h>
#include "rlbidi_version.h"
#define __STR(x) #x
#define STRINGIFY(x) __STR(x)
#ifndef RLBIDI_VERSION
#	define RLBIDI_VERSION "?.?.?"
#endif
#if PY_MAJOR_VERSION < 3
#	error "rlbidi " RLBIDI_VERSION " needs python 3"
#endif
#include <fribidi.h>
#ifdef Py_LIMITED_API
#	define RLPYUNICODE_GETLENGTH(u) PyUnicode_GetLength(u)
#else
#	define RLPYUNICODE_GETLENGTH(u) PyUnicode_GET_LENGTH(u)
#endif

static Py_ssize_t _checkOptionalList(const char* name, PyObject *obj, void **ptr, size_t nelem, size_t elsize){
	if(!obj || obj==Py_None) return 1;
	if(PyList_SetSlice(obj, 0, PY_SSIZE_T_MAX, NULL)<0){
		PyErr_Clear();
		PyErr_Format(PyExc_TypeError,"Argument %s is of wrong type", name);
		return 0;
		}
	*ptr = PyMem_Calloc(nelem,elsize);
	if(!*ptr){
		PyErr_Clear();
		PyErr_Format(PyExc_MemoryError,"Argument %s storage allocation failed", name);
		return 0;
		}
	return 2;
	}
static PyObject *DeletePyList(PyObject *L){
	if(L){
		PyList_SetSlice(L, 0, PY_SSIZE_T_MAX, NULL);
		Py_DecRef(L);
	}
	return NULL;
}

static PyObject * _rlbidi_log2vis(PyObject * self, PyObject * args, PyObject * kw){
	PyObject *u=NULL;	/* input unicode or string object */
	FriBidiParType base = FRIBIDI_TYPE_RTL;	/* optional direction */
	PyObject *positions_L_to_V=NULL, *positions_V_to_L=NULL, *embedding_levels=NULL;
	int clean = 0; /* optional flag to clean the string */
	int reordernsm = 1; /* optional flag to allow reordering of non spacing marks*/

	static char *kwargs[] = { "logical", "base_direction", "clean", "reordernsm", "positions_L_to_V", "positions_V_to_L", "embedding_levels", NULL };

	if(!PyArg_ParseTupleAndKeywords(args, kw, "U|iiiOOO", kwargs,
				&u, &base, &clean, &reordernsm, &positions_L_to_V, &positions_V_to_L, &embedding_levels)
			) return NULL;

	/* Validate base */
	if(!(base == (FriBidiParType)FRIBIDI_TYPE_RTL
	  || base == (FriBidiParType)FRIBIDI_TYPE_LTR
	  || base == (FriBidiParType)FRIBIDI_TYPE_ON
	  || base == (FriBidiParType)FRIBIDI_TYPE_WRTL
	  || base == (FriBidiParType)FRIBIDI_TYPE_WLTR
	  ))
		return PyErr_Format(PyExc_ValueError, "invalid value %d: use either RTL, LTR or ON", base);

	Py_ssize_t length = RLPYUNICODE_GETLENGTH(u), i;
	FriBidiChar *logical = NULL;	/* input fribidi unicode buffer */
	FriBidiChar *visual = NULL;		/* output fribidi unicode buffer */
	FriBidiStrIndex *L_to_V = NULL;
	FriBidiStrIndex *V_to_L = NULL;
	FriBidiLevel *levels = NULL;
	PyObject *obj;
	int	r;

	PyObject *result = NULL;

	if(!_checkOptionalList("positions_L_to_V",positions_L_to_V, (void**)&L_to_V, length+1, sizeof(FriBidiStrIndex))) return NULL;
	if(!_checkOptionalList("positions_V_to_L",positions_V_to_L,(void**)&V_to_L, length+1, sizeof(FriBidiStrIndex))) return NULL;
	if(!_checkOptionalList("embedding_levels",embedding_levels,(void**)&levels, length+1, sizeof(FriBidiLevel))) return NULL;

	/* Allocate fribidi unicode buffers
	   TODO - Don't copy strings if sizeof(FriBidiChar) == sizeof(Py_UNICODE)
	*/
	if(!(logical=PyMem_New(FriBidiChar, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}

	if(!(visual=PyMem_New(FriBidiChar, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}

#ifdef Py_LIMITED_API
	for(i=0; i<length; ++i){
		logical[i] = PyUnicode_ReadChar(u,i);
		}
#else
	void *data = NULL;
	int	kind;
	if(PyUnicode_READY(u)) goto cleanup;
	data = PyUnicode_DATA(u);
	kind = PyUnicode_KIND(u);
	for(i=0; i<length; ++i){
		logical[i] = PyUnicode_READ(kind,data,i);
		}
#endif

	/* Convert to unicode and order visually */
	fribidi_set_reorder_nsm(reordernsm);

	if(!fribidi_log2vis(logical, (const FriBidiStrIndex)length, &base, visual, L_to_V, V_to_L, levels)){
		PyErr_SetString(PyExc_RuntimeError, "fribidi failed to order string");
		goto cleanup;
		}

	/* Cleanup the string if requested */
	if(clean) length = fribidi_remove_bidi_marks(visual, (const FriBidiStrIndex)length,  L_to_V, V_to_L, levels);
#ifdef Py_LIMITED_API
	result = PyUnicode_DecodeUTF32((const char *)visual, length*4, "strict", NULL);
#else
	result = PyUnicode_FromKindAndData(PyUnicode_4BYTE_KIND,(void*)visual, length);
#endif
	if(L_to_V){
		for(i=0;i<length;i++){
			if(!(obj = PyLong_FromLong((long)L_to_V[i]))) goto cleanup;
			r = PyList_Append(positions_L_to_V,obj);
			Py_DecRef(obj);
			if(r<0) goto cleanup;
			}
		}
	if(V_to_L){
		for(i=0;i<length;i++){
			if(!(obj = PyLong_FromLong((long)V_to_L[i]))) goto cleanup;
			r = PyList_Append(positions_V_to_L,obj);
			Py_DecRef(obj);
			if(r<0) goto cleanup;
			}
		}
	if(levels){
		for(i=0;i<length;i++){
			if(!(obj = PyLong_FromLong((long)levels[i]))) goto cleanup;
			r = PyList_Append(embedding_levels,obj);
			Py_DecRef(obj);
			if(r<0) goto cleanup;
			}
		}

cleanup:
	/* Delete unicode buffers */
	PyMem_Del(logical);
	PyMem_Del(visual);
	PyMem_Del(L_to_V);
	PyMem_Del(V_to_L);
	PyMem_Del(levels);

	return (PyObject *)result;
	}

PyObject *_rlbidi_reorderMap(PyObject * self, PyObject * args){
	PyObject *u, *roMapList=NULL, *obj;
	if(!PyArg_ParseTuple(args, "U", &u)) return NULL;

	FriBidiChar *logical = NULL;	/* input fribidi unicode buffer */
	FriBidiChar *visual = NULL;		/* output fribidi unicode buffer */
	FriBidiStrIndex *roMap = NULL;
	FriBidiCharType *cTypes = NULL;
	FriBidiLevel *levels = NULL;
	FriBidiJoiningType *jTypes = NULL;
	FriBidiArabicProp *arProps = NULL;
	int r;

	Py_ssize_t length = RLPYUNICODE_GETLENGTH(u), i;
	if(!(logical=PyMem_New(FriBidiChar, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}
	if(!(visual=PyMem_New(FriBidiChar, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}
	if(!(roMap=PyMem_New(FriBidiStrIndex, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}
	if(!(cTypes=PyMem_New(FriBidiCharType, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}
	if(!(levels=PyMem_New(FriBidiLevel, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}
	if(!(jTypes=PyMem_New(FriBidiJoiningType, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}
	if(!(arProps=PyMem_New(FriBidiArabicProp, length + 1))){
		PyErr_NoMemory();
		goto cleanup;
		}

#ifdef Py_LIMITED_API
	for(i=0; i<length; ++i){
		logical[i] = PyUnicode_ReadChar(u,i);
		}
#else
	void *data = NULL;
	int	kind;
	if(PyUnicode_READY(u)) goto cleanup;
	data = PyUnicode_DATA(u);
	kind = PyUnicode_KIND(u);
	for(i=0; i<length; ++i){
		logical[i] = PyUnicode_READ(kind,data,i);
		}
#endif

	// Get letter types.
	fribidi_get_bidi_types(logical, length, cTypes);

	FriBidiParType baseDirection = FRIBIDI_PAR_LTR;
	FriBidiLevel   Py_UNUSED(resolveParDir) = fribidi_get_par_embedding_levels(cTypes, length, &baseDirection, levels);

	// joine types.
	fribidi_get_joining_types(logical, length, jTypes);

	// arabic join.
	memcpy(arProps, jTypes, length * sizeof(FriBidiJoiningType));
	fribidi_join_arabic(cTypes, length, levels, arProps);

	// shapes.
	fribidi_shape (FRIBIDI_FLAG_SHAPE_MIRRORING | FRIBIDI_FLAG_SHAPE_ARAB_PRES | FRIBIDI_FLAG_SHAPE_ARAB_LIGA,
				   levels, length, arProps, logical);

	memcpy(visual, logical, length*sizeof(FriBidiChar));
	for(i = 0;i<length;i ++){
		roMap[i] = i;
	}

	FriBidiLevel Py_UNUSED(_levels) = fribidi_reorder_line(FRIBIDI_FLAGS_ARABIC, cTypes, length,
											0, baseDirection,  levels, visual, roMap);

	if(!(roMapList=PyList_New(0))) goto cleanup;
	for(i=0;i<length;i++){
		if(!(obj = PyLong_FromLong((long)roMap[i]))) goto cleanup1;
		r = PyList_Append(roMapList,obj);
		Py_DecRef(obj);
		if(r<0) goto cleanup1;
		}

cleanup:
	/* Delete unicode buffers */
	PyMem_Del(logical);
	PyMem_Del(visual);
	PyMem_Del(roMap);
	PyMem_Del(cTypes);
	PyMem_Del(levels);
	PyMem_Del(jTypes);
	PyMem_Del(arProps);

	return roMapList;
cleanup1:
	roMapList = DeletePyList(roMapList);
	goto cleanup;
    }

static PyMethodDef rlbidiMethods[] = {
	{"log2vis", (PyCFunction) _rlbidi_log2vis, METH_VARARGS | METH_KEYWORDS, NULL},
	{"reorderMap", (PyCFunction) _rlbidi_reorderMap, METH_VARARGS, NULL},
	{NULL, NULL, 0, NULL}
	};

static struct PyModuleDef moduledef={
	PyModuleDef_HEAD_INIT,
	"_rlbidi",
	NULL,
	0,
	rlbidiMethods,
	NULL,
	NULL,
	NULL,
	NULL
	};

PyMODINIT_FUNC PyInit__rlbidi(void){
	PyObject *module=NULL;
	module = PyModule_Create(&moduledef);
	if(!module) goto err;
	if(		PyModule_AddIntConstant(module, "RTL", (long)FRIBIDI_TYPE_RTL)
		||	PyModule_AddIntConstant(module, "LTR", (long)FRIBIDI_TYPE_LTR)
		||	PyModule_AddIntConstant(module, "ON", (long)FRIBIDI_TYPE_ON)
		||	PyModule_AddIntConstant(module, "WLTR", (long)FRIBIDI_PAR_WLTR)
		||	PyModule_AddIntConstant(module, "WRTL", (long)FRIBIDI_PAR_WRTL)
		||	PyModule_AddStringConstant(module, "rlbidiVersion", (const char *)STRINGIFY(RLBIDI_VERSION))
		||	PyModule_AddStringConstant(module, "fribidiVersion", (const char *)FRIBIDI_VERSION)
		||	PyModule_AddStringConstant(module, "fribidiInterfaceVersion", (const char *)FRIBIDI_INTERFACE_VERSION_STRING)
		||	PyModule_AddStringConstant(module, "fribidiUnicodeVersion", (const char *)FRIBIDI_UNICODE_VERSION)
		)
		goto err;
	return module;
err:/*Check for errors*/
	Py_XDECREF(module);
	return NULL;
	}
