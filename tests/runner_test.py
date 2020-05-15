from os import sep
from unittest import TestCase
from unittest import main

from checking import runner as r
from checking.classes.basic_test import Test
from checking.classes.basic_group import TestGroup
from checking.classes.basic_suite import TestSuite
from checking.classes.listeners.basic import Listener
from checking.exceptions import UnknownProviderName, TestIgnoredException

from tests.fixture_behaviour_test import clear


class TestListener(Listener):
    def on_failed(self, group: TestGroup, test: TestCase, exception_: Exception):
        global COUNT
        COUNT = COUNT + 2

    def on_broken(self, group: TestGroup, test: TestCase, exception_: Exception):
        global COUNT
        COUNT = COUNT + 3

    def on_ignored_by_condition(self, group: TestGroup, test: TestCase, exc: Exception):
        global COUNT
        COUNT = COUNT + 4


COUNT = 0


def inc():
    global COUNT
    COUNT += 1


def fail_assert():
    raise AssertionError()


def fail_exception():
    raise ValueError()


def fail_test():
    raise TestIgnoredException


class RunnerTest(TestCase):
    r._listener = TestListener()

    def test_run_fixture_true(self):
        result = r._run_fixture(r._fake, 'test', 'test')
        self.assertFalse(result)

    def test_run_fixture_false(self):
        result = r._run_fixture(lambda: int('a'), 'test', 'test')
        self.assertTrue(result)

    def test_run_after_runs_for_test(self):
        test_case = Test('test', inc)
        test_case.add_after(inc)
        count = COUNT
        r._run_after(test_case)
        self.assertEqual(count + 1, COUNT)

    def test_run_after_runs_for_group(self):
        test_case = TestGroup('test')
        test_case.add_after(inc)
        count = COUNT
        r._run_after(test_case)
        self.assertEqual(count + 1, COUNT)

    def test_run_after_runs_for_test_if_before_failed(self):
        test_case = Test('test', inc)
        test_case.add_after(inc)
        test_case.is_before_failed = True
        count = COUNT
        r._run_after(test_case)
        self.assertEqual(count, COUNT)

    def test_run_after_runs_for_group_if_before_failed(self):
        test_case = TestGroup('test')
        test_case.add_after(inc)
        test_case.is_before_failed = True
        count = COUNT
        r._run_after(test_case)
        self.assertEqual(count, COUNT)

    def test_run_after_runs_for_test_if_before_failed_but_always_run(self):
        test_case = Test('test', inc)
        test_case.add_after(inc)
        test_case.is_before_failed = True
        test_case.always_run_after = True
        count = COUNT
        r._run_after(test_case)
        self.assertEqual(count + 1, COUNT)

    def test_run_after_runs_for_group_if_before_failed_but_always_run(self):
        test_case = TestGroup('test')
        test_case.add_after(inc)
        test_case.is_before_failed = True
        test_case.always_run_after = True
        count = COUNT
        r._run_after(test_case)
        self.assertEqual(count + 1, COUNT)

    def test_run_before_for_test_be_false(self):
        test_case = Test('test', inc)
        test_case.add_before(r._fake)
        r._run_before(test_case)
        self.assertFalse(test_case.is_before_failed)

    def test_run_before_for_group_be_false(self):
        test_case = TestGroup('test')
        test_case.add_before(r._fake)
        r._run_before(test_case)
        self.assertFalse(test_case.is_before_failed)

    def test_run_before_for_test_be_true(self):
        test_case = Test('test', inc)
        test_case.add_before(lambda: int('a'))
        r._run_before(test_case)
        self.assertTrue(test_case.is_before_failed)

    def test_run_before_for_group_be_true(self):
        test_case = TestGroup('test')
        test_case.add_before(lambda: int('a'))
        r._run_before(test_case)
        self.assertTrue(test_case.is_before_failed)

    def test_check_providers_returns_if_empty(self):
        clear()
        suite = TestSuite.get_instance()
        r._check_data_providers(suite)

    def test_check_providers_returns_ok_if_exists(self):
        clear()
        suite = TestSuite.get_instance()
        suite.providers['test'] = print
        test_case = Test('test', inc)
        test_case.provider = 'test'
        suite.get_or_create("group").add_test(test_case)
        r._check_data_providers(suite)

    def test_check_providers_returns_failed_if_not_exists(self):
        clear()
        suite = TestSuite.get_instance()
        suite.providers['test'] = print
        test_case = Test('test', inc)
        test_case.provider = 'test2'
        suite.get_or_create("group").add_test(test_case)
        with self.assertRaises(UnknownProviderName):
            r._check_data_providers(suite)

    def test_run_test_ok(self):
        test_case = Test('test', inc)
        count = COUNT
        self.assertTrue(r._run_test(test_case, TestGroup("group")))
        self.assertEqual(count + 1, COUNT)

    def test_run_test_assert_fail(self):
        test_case = Test('test', fail_assert)
        self.assertFalse(r._run_test(test_case, TestGroup("group")))

    def test_run_test_assert_broken(self):
        test_case = Test('test', fail_exception)
        self.assertFalse(r._run_test(test_case, TestGroup("group")))

    def test_run_test_assert_ignored(self):
        test_case = Test('test', fail_test)
        self.assertFalse(r._run_test(test_case, TestGroup("group")))

    def test_provider_next_iter(self):
        clear()
        TestSuite.get_instance().providers['test2'] = lambda: [1, 2, 3]
        cycle = r._provider_next('test2')
        self.assertEqual('123', ''.join([str(_) for _ in cycle]))

    def test_provider_next_closeable(self):
        class Fake:
            def __next__(self):
                return 1

            def __iter__(self):
                return iter([1])

            def close(self):
                global COUNT
                COUNT = COUNT + 6

        clear()
        count = COUNT
        TestSuite.get_instance().providers['test2'] = Fake
        cycle = r._provider_next('test2')
        self.assertEqual('1', ''.join([str(_) for _ in cycle]))
        self.assertEqual(count + 6, COUNT)

    def test_run_all_test_in_group(self):
        test_case = Test('one', inc)
        test_case2 = Test('two', inc)
        group = TestGroup('group')
        count = COUNT
        group.add_test(test_case)
        group.add_test(test_case2)
        r._run_all_tests_in_group(group)
        self.assertEqual(count + 2, COUNT)


if __name__ == '__main__':
    main()
