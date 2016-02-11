# -*- coding: utf-8 -*-
import inspect
import logging
import unittest
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException


class FaExportSelenium(unittest.TestCase):
    def setUp(self):
        if False:
            self.driver = webdriver.Firefox()
        else:
            self.driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")
        self.driver.implicitly_wait(30)
        self.base_url = "http://www.filmaffinity.com/"
        self.verificationErrors = []
        self.accept_next_alert = True

    @staticmethod
    def get_text_excluding_children(driver, element):
        return driver.execute_script("""
var parent = arguments[0];
var child = parent.firstChild;
var ret = "";
while(child) {
    if (child.nodeType === Node.TEXT_NODE)
        ret += child.textContent;
    child = child.nextSibling;
}
return ret;
""", element)

    class Movie:
        pass

    def __get_movie_from_title(self, driver, title):
        title_elements_a = title.find_elements_by_tag_name('a')
        assert len(title_elements_a) == 1
        for tea in title_elements_a:
            titulo_peli = tea.text
            pass
        title_elements_all = title.find_elements_by_xpath('*')
        joajo = len(title_elements_all)
        for teall in title_elements_all:
            if teall.tag_name == 'a':
                continue
            pass
        nanana = self.__class__.get_text_excluding_children(driver, title)
        s1 = nanana.strip().replace('(', '').replace(')', '')
        anio = int(s1)
        dire = title.find_element_by_xpath("./following-sibling::div")
        director = dire.text
        commonparent = title.find_element_by_xpath('../../../..')

        blu333 = commonparent.find_elements_by_xpath('*')
        for a222 in blu333:
            c12 = a222.get_attribute('class')
            if c12 == 'my-votes-rating-box':
                pass
                for c14 in a222.find_elements_by_xpath('*'):
                    c15 = c14.get_attribute('class')
                    if c15 == 'rate-movie-box':
                        rating = c14.get_attribute('data-user-rating')
                        id1 = c14.get_attribute('data-movie-id')
                        pass
                    pass
            pass
        if False:
            select = commonparent.find_element_by_class('my-votes-rating-box')
            select = commonparent.find_element_by_class('rating-select')
            select2 = commonparent.find_element_by_tag('select')
        mov = self.Movie()
        mov.title = titulo_peli
        mov.anio = anio
        mov.id = id1
        mov.rating = rating
        mov.director = director
        return mov
        pass

    def __get_movies_in_page(self, driver):
        titles = driver.find_elements_by_class_name('mc-title')
        for title in titles:
            mov = self.__get_movie_from_title(driver, title)
            yield mov
        pass

    def __get_movies(self):
        driver = self.driver
        driver.get(self.base_url + "es/main.html")
        driver.find_element_by_link_text(u"Iniciar sesión").click()
        driver.find_element_by_name("username").clear()
        import config
        driver.find_element_by_name("username").send_keys(config.fauser)
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys(config.fapass)
        driver.find_element_by_name("ok").click()
        driver.find_element_by_link_text(u"críticas").click()
        driver.find_element_by_link_text("Mis votaciones").click()
        var2 = driver.find_element_by_css_selector("#mt-content-cell > table > tbody > tr > td").text
        pagcount = int(var2.split(' de ')[1])
        for current_page in range(1, pagcount + 1):
            driver.get(self.base_url + "es/myvotes.php?p={}&orderby=4".format(current_page))
            for mov in self.__get_movies_in_page(driver):
                yield mov
        pass

    def test_blabla(self):
        for a in self.__get_movies():
            pass

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException, e:
            return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

    def main_get_movies(self):
        self.setUp()
        for a in self.__get_movies():
            yield a
        self.tearDown()


def get_user_attributes(cls):
    boring = dir(type('dummy', (object,), {}))
    return [item[0]
            for item in inspect.getmembers(cls)
            if item[0] not in boring]


class CSVwrite1:
    pass

    @classmethod
    def __get_logger(cls):
        return logging.getLogger(__name__ + '.' + cls.__name__)

    def writeObjects(self, objects_):
        file_name = 'fa.csv'
        import unicodecsv as csv
        with open(file_name, 'w') as csvfile:
            writer = None
            for object_ in objects_:
                if writer is None:
                    fn = get_user_attributes(object_)
                    writer = csv.DictWriter(csvfile, fieldnames=fn, encoding='utf-8')
                    writer.writeheader()
                ddd = object_.__dict__
                self.__get_logger().info('about to write {}'.format(object_.id))
                writer.writerow(ddd)
                pass
        pass


if __name__ == "__main__":
    if False:
        unittest.main()
    else:
        f = FaExportSelenium('test_blabla')
        w = CSVwrite1()
        w.writeObjects(f.main_get_movies())
        pass
