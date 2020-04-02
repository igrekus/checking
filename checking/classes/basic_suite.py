from typing import Dict, List, Callable, Iterable

from .basic_group import TestGroup
from .basic_test import Test


class TestSuite:
    """
    The run class, test suite, always in a single instance (singleton), includes all sets.
    If there is at least 1 test, then it includes 1 group.
    """
    instance = None

    # The dictionary pairs name of set-set
    groups: Dict[str, TestGroup] = {}

    # Data providers (allow to all tests in all sets)
    providers: Dict[str, Callable[[None], Iterable]] = {}

    # Lists of functions which execute before and after run
    before: List[Callable] = []
    after: List[Callable] = []
    name: str = 'Default Test Suite'

    # Flags that preliminary functions fell
    is_before_failed: bool = False

    # The flag that the final functions should be performed regardless of the result of preliminary
    always_run_after: bool = False

    def __new__(cls):
        if not cls.instance:
            cls.instance = super(TestSuite, cls).__new__(cls)
        return cls.instance

    @classmethod
    def add_before(cls, func: Callable):
        cls.before.append(func)

    @classmethod
    def add_after(cls, func: Callable):
        cls.after.append(func)

    @classmethod
    def get_instance(cls):
        return TestSuite()

    @classmethod
    def get_or_create(cls, group_name: str) -> TestGroup:
        """
        It creates and returns a test group by name.
        :param group_name: is the name of group
        :return: TestGroup
        """
        if group_name not in cls.groups:
            cls.groups[group_name] = TestGroup(group_name)
        return cls.groups[group_name]

    @classmethod
    def filter_groups(cls, groups: List[str]):
        cls.groups = {name: tests for name, tests in cls.groups.items() if name in groups}

    @classmethod
    def is_empty(cls) -> bool:
        """
        It returns whether the suite is empty (no tests in any of the groups).
        :return: True if there are no tests
        """
        return all([group.is_empty() for group in cls.groups.values()])

    @classmethod
    def tests_count(cls) -> int:
        """
        Returns the total number of tests. Only tests with the parameter enabled=True get into the set.
        :return: is the number of the tests
        """
        if cls.is_empty():
            return 0
        return sum([group.tests_count() for group in cls.groups.values()])

    @classmethod
    def success(cls) -> List[Test]:
        """
        Returns the list of successful tests.
        :return:
        """
        return cls._test_result_of('success')

    @classmethod
    def failed(cls) -> List[Test]:
        """
        Returns the list of fell tests.
        :return:
        """
        return cls._test_result_of('failed')

    @classmethod
    def broken(cls) -> List[Test]:
        """
        Returns the list of broken tests (fell by exception, not by assert).
        :return:
        """
        return cls._test_result_of('broken')

    @classmethod
    def ignored(cls) -> List[Test]:
        """
        Returns the list of ignored tests (unsuccessful preliminary functions).
        :return:
        """
        return cls._test_result_of('ignored')

    @classmethod
    def _test_result_of(cls, name: str) -> List[Test]:
        return [test for group in cls.groups.values() for test in group.test_results[name]]
