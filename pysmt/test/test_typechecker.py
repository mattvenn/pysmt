#
# This file is part of pySMT.
#
#   Copyright 2014 Andrea Micheli and Marco Gario
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from pysmt.typing import REAL, BOOL, INT, FunctionType
from pysmt.type_checker import QuantifierOracle
from pysmt.type_checker import (assert_no_boolean_in_args,
                                assert_boolean_args,
                                assert_same_type_args,
                                assert_args_type_in)
from pysmt.shortcuts import (Symbol, And, Plus, Minus, Times, Equals, Or, Iff,
                             LE, LT, Not, GE, GT, Ite, Bool, Int, Real, Div,
                             Function)
from pysmt.shortcuts import get_env
from pysmt.test import TestCase
from pysmt.test.examples import EXAMPLE_FORMULAS
from pysmt.decorators import typecheck_result


class TestSimpleTypeChecker(TestCase):

    def setUp(self):
        super(TestSimpleTypeChecker, self).setUp()

        self.tc = get_env().stc
        self.x = Symbol("x", BOOL)
        self.y = Symbol("y", BOOL)
        self.p = Symbol("p", INT)
        self.q = Symbol("q", INT)
        self.r = Symbol("r", REAL)
        self.s = Symbol("s", REAL)

        self.qfo = get_env().qfo


    def test_boolean(self):
        varA = Symbol("At", INT)
        varB = Symbol("Bt", INT)

        f = And(LT(varA, Plus(varB, Int(1))),
                GT(varA, Minus(varB, Int(1))))
        g = Equals(varA, varB)
        h = Iff(f, g)

        tc = get_env().stc
        res = tc.walk(h)
        self.assertEquals(res, BOOL)


    def test_functions(self):
        vi = Symbol("At", INT)
        vr = Symbol("Bt", REAL)

        f = Symbol("f", FunctionType(INT, [REAL]))
        g = Symbol("g", FunctionType(REAL, [INT]))

        tc = get_env().stc

        self.assertEquals(tc.walk(Function(f, [vr])), INT)
        self.assertEquals(tc.walk(Function(g, [vi])), REAL)
        self.assertEquals(tc.walk(Function(f, [Function(g, [vi])])), INT)
        self.assertEquals(tc.walk(LE(Plus(vi, Function(f, [Real(4)])), Int(8))), BOOL)
        self.assertEquals(tc.walk(LE(Plus(vr, Function(g, [Int(4)])), Real(8))), BOOL)

        with self.assertRaises(TypeError):
            LE(Plus(vr, Function(g, [Real(4)])), Real(8))

        with self.assertRaises(TypeError):
            LE(Plus(vi, Function(f, [Int(4)])), Int(8))



    def test_walk_type_to_type(self):
        # TODO: this exploits a private service of the type checker,
        # we should test the external interface
        f = self.x
        args1 = [BOOL, BOOL]
        args2 = [BOOL, REAL]
        args3 = [None, None]

        t = self.tc.walk_type_to_type(f, args1, BOOL, REAL)
        self.assertEquals(t, REAL)

        t = self.tc.walk_type_to_type(f, args2, BOOL, REAL)
        self.assertEquals(t, None)

        t = self.tc.walk_type_to_type(f, args3, BOOL, REAL)
        self.assertEquals(t, None)

    def test_misc(self):
        bool_list = [
            And(self.x, self.y),
            Or(self.x, self.y),
            Not(self.x),
            self.x,
            Equals(self.p, self.q),
            GE(self.p, self.q),
            LE(self.p, self.q),
            GT(self.p, self.q),
            LT(self.p, self.q),
            Bool(True),
            Ite(self.x, self.y, self.x)
        ]

        # TODO: FORALL EXISTS
        real_list = [
            self.r,
            Real(4),
            Plus(self.r, self.s),
            Plus(self.r, Real(2)),
            Minus(self.s, self.r),
            Times(self.r, Real(1)),
            Div(self.r, Real(1)),
            Ite(self.x, self.r, self.s),
        ]

        int_list = [
            self.p,
            Int(4),
            Plus(self.p, self.q),
            Plus(self.p, Int(2)),
            Minus(self.p, self.q),
            Times(self.p, Int(1)),
            Ite(self.x, self.p, self.q),
        ]

        for f in bool_list:
            t = self.tc.walk(f)
            self.assertEqual(t, BOOL, f)

        for f in real_list:
            t = self.tc.walk(f)
            self.assertEqual(t, REAL, f)

        for f in int_list:
            t = self.tc.walk(f)
            self.assertEqual(t, INT, f)


    def test_quantifier_oracle(self):
        oracle = self.qfo
        for (f, _, _, logic) in EXAMPLE_FORMULAS:
            is_qf = oracle.is_qf(f)
            self.assertEqual(is_qf, logic.quantifier_free, f)


    def test_assert_args(self):
        assert_no_boolean_in_args([self.r, self.p])
        with self.assertRaises(TypeError):
            assert_no_boolean_in_args([self.x, self.y])

        assert_boolean_args([self.x, self.y])
        with self.assertRaises(TypeError):
            assert_boolean_args([self.r, self.p])

        assert_same_type_args([self.x, self.y])
        with self.assertRaises(TypeError):
            assert_same_type_args([self.r, self.p])

        assert_args_type_in([self.x, self.p],
                            allowed_types=[INT, BOOL])
        with self.assertRaises(TypeError):
            assert_args_type_in([self.x, self.p],
                                allowed_types=[REAL, BOOL])


    def test_decorator_typecheck_result(self):
        @typecheck_result
        def good_function():
            return self.x

        @typecheck_result
        def super_bad_function():
            sb = And(self.x, self.y)
            # !!! This hurts so badly  !!!
            # !!! Do not try this at home !!!
            sb._content.args[0] = self.p
            return sb

        good_function()

        with self.assertRaises(TypeError):
            super_bad_function()

if __name__ == '__main__':
    import unittest
    unittest.main()