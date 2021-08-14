from time import sleep
import config
from selenium import webdriver
import vk_api
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from vk_api.utils import get_random_id
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as ec

options = Options()
options.add_argument("--headless")
browser = webdriver.Chrome(options=options)
browser.get("https://new.mospolytech.ru/postupayushchim/priem-v-universitet/rating-abiturientov/")
vk_session = vk_api.VkApi(
    token=config.vk_token)
vk = vk_session.get_api()


# жмет на кнопки чтобы получить конкурсный список по направлению
def to_table(direction):
    Select(browser.find_element_by_name("select1")).select_by_value("000000017_01")
    select = Select(browser.find_element_by_name("select2"))
    options = [option.text for option in select.options]
    name = [i for i in options if direction in i][0]
    select.select_by_visible_text(name)
    Select(browser.find_element_by_name("eduForm")).select_by_value("Очная")
    Select(browser.find_element_by_name("eduFin")).select_by_value("Бюджетная основа")
    browser.find_elements_by_id("FIObutton")[0].click()
    sleep(1)
    WebDriverWait(browser, 30).until(ec.presence_of_element_located((By.ID, "div4")))


# получаем то, что появилось на странице, после выполнения функции выше
def get_search_results():
    return browser.find_element_by_id("ps_search_results")


class Abitur:
    all_dirs = set()

    def __init__(self, name, delo: int, dirs: tuple, vk_id: int):
        self.name = name
        self.delo = delo
        self.dirs = dirs
        self.last = [(0, 0) for _ in range(len(dirs))]
        self.vk_id = vk_id
        for direction in self.dirs:
            Abitur.all_dirs.add(direction)

    def in_direction(self, direction):
        return direction in self.dirs

    # Проверяет на наличие изменений в местах, и если они есть, то присылает сообщение
    def work(self, results, direction):
        ind = self.dirs.index(direction)
        if results != self.last[ind]:
            self.last[ind] = results
            self.send_msg(f"Политех: Изменения\n"
                          f"{direction}: {results[0]}/{results[1]}\n")

    # Отправить сообщение вк
    def send_msg(self, msg):
        vk.messages.send(
            user_id=self.vk_id,
            random_id=get_random_id(),
            message=msg
        )
        print(f"{self.name}: {msg}")


# получает количество бюджетных мест, хотя тут оно не меняется, пока не зачислят особенных
# после зачисления оно поменяется, но все равно менятся не должно
def get_mest(table):
    el = table.find_elements_by_tag_name("li")[7].text
    return int(el.split()[-1])


# прикол а не код
# получаем табличку ищем нас с помощью xpath
# если у нас есть рейтинг возвращаем его
# иначе идем вверх. как только получаем кого то с реальным рейтингом
# возвращаем его + 1
# если в реальном рейтинге не число, значит мы уже в самом вверху, а потому возвращаем единичку
# иначе если рак на горе свистнул возвращаем -1337
def get_place(table, delo):
    table = table.find_elements_by_tag_name("table")[4]
    row = table.find_element_by_xpath(f"//td[contains(text(), '{delo}')]").find_element_by_xpath('..')
    cols = row.find_elements_by_tag_name('td')
    if cols[1].text.strip():
        return int(cols[1].text.strip())
    rows = row.find_elements_by_xpath("./preceding-sibling::tr")[::-1]
    for i in rows:
        cols = i.find_elements_by_tag_name('td')
        if cols[1].text.strip():
            if cols[1].text.strip().isdigit():
                return int(cols[1].text.strip()) + 1
            return 1
    return -1337


if __name__ == '__main__':
    abiturs = [  # Имя  # номер дела в лк # кортеж направлений # айди в вк
        Abitur("Имя", 41279, ("23.05.01.02",), 111111111),
        Abitur("Имя", 41279, ("23.05.01.02",), 111111111),
        Abitur("Имя", 41279, ("23.05.01.02",), 111111111),
    ]
    for man in abiturs:
        man.send_msg("Политех перезапуск\n\n")


    def megawork():
        try:
            for direction in Abitur.all_dirs:
                to_table(direction)
                res = get_search_results()
                mest = get_mest(res)
                for abitur in abiturs:
                    if abitur.in_direction(direction):
                        results = [get_place(res, abitur.delo), mest]
                        abitur.work(results, direction)
            print("Закончил круг")  # можете убрать мне прикольно
            browser.refresh()
            sleep(3)
        except:
            megawork()


    while True:
        megawork()

browser.close()
