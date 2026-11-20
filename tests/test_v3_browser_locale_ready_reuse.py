"""BSA231: reuse historical BSA128 locale-load readiness in V3 browser QA.

These are synthetic guard/fault tests, not actual Chrome acceptance. The real
one-section Yoga6 probe and full normal worker are separate validation.
"""
import inspect
from unittest.mock import patch
import unittest

from scripts import check_v3_real_chapter9_browser as browser


class FakeDriver:
    def __init__(self,enabled_after=1,question_after=1):
        self.tick=0
        self.enabled_after=enabled_after
        self.question_after=question_after
        self.select_calls=[]
    def find_element(self,how,name):
        if name!="locale":
            raise AssertionError("unexpected element: "+str(name))
        return FakeLocale(self)
    def find_elements(self,how,name):
        if name!="#app h1.question":
            raise AssertionError("wrong question selector")
        return [object()] if self.tick>=self.question_after else []


class FakeLocale:
    def __init__(self,driver):
        self.driver=driver
    def is_enabled(self):
        return self.driver.tick>=self.driver.enabled_after


class FakeWebDriverWait:
    def __init__(self,driver,seconds):
        self.driver=driver
        self.seconds=seconds
    def until(self,condition):
        for tick in range(6):
            self.driver.tick=tick
            if condition(self.driver):
                return True
        raise TimeoutError("locale never ready")


class FakeSelect:
    def __init__(self,element):
        self.element=element
    def select_by_value(self,value):
        if not self.element.is_enabled():
            raise NotImplementedError("Selecting a disabled option")
        self.element.driver.select_calls.append((self.element.driver.tick,value))


class V3LocaleReadinessRecoveryTests(unittest.TestCase):
    def test_disabled_selector_refused_even_if_question_exists(self):
        driver=FakeDriver(enabled_after=99,question_after=0)
        driver.tick=4
        self.assertFalse(browser._locale_loaded_and_enabled(driver))

    def test_missing_question_refused_even_if_selector_enabled(self):
        driver=FakeDriver(enabled_after=0,question_after=99)
        driver.tick=4
        self.assertFalse(browser._locale_loaded_and_enabled(driver))

    def test_ready_requires_both_before_selecting(self):
        driver=FakeDriver(enabled_after=2,question_after=3)
        with patch("selenium.webdriver.support.ui.WebDriverWait",FakeWebDriverWait),patch(
            "selenium.webdriver.support.ui.Select",FakeSelect):
            browser._select_loaded_locale(driver,"ms")
        self.assertEqual(driver.select_calls,[(3,"ms")])

    def test_never_ready_fails_without_select(self):
        driver=FakeDriver(enabled_after=99,question_after=0)
        with patch("selenium.webdriver.support.ui.WebDriverWait",FakeWebDriverWait),patch(
            "selenium.webdriver.support.ui.Select",FakeSelect):
            with self.assertRaisesRegex(TimeoutError,"never ready"):
                browser._select_loaded_locale(driver,"zh")
        self.assertEqual(driver.select_calls,[])

    def test_source_candidate_browser_reuses_single_shared_guard(self):
        source=inspect.getsource(browser._exercise)
        self.assertEqual(source.count("_select_loaded_locale(driver,"),3)
        self.assertNotIn('Select(driver.find_element(By.ID,"locale")',source)

if __name__=="__main__":
    unittest.main()
