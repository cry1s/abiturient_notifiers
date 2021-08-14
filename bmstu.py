import requests as r
import config
from tika import parser
import vk_api
from vk_api.utils import get_random_id

vk_session = vk_api.VkApi(
    token=config.vk_token)
vk = vk_session.get_api()


# получая кортеж направлений на вход, скачивает их и возвращает названия файлов
def get_pdfs(dirs):
    r = []
    for dir in dirs:
        url = f'https://priem.bmstu.ru/lists/upload/enrollees/first/moscow-1/{dir}.pdf'
        r.append(download_file(url))
    return r


# скачивает файл и пытается это сделать пока не скачает, возвращает название файла
def download_file(url):
    try:
        local_filename = url.split('/')[-1]
        with r.get(url, stream=True) as page:
            page.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in page.iter_content(chunk_size=None):
                    if chunk:
                        f.write(chunk)
        return local_filename
    except:
        download_file(url)


# достает текст из пдфа, гонит до начала списка общего конкурса, оттуда получает количество мест
# далее ищет по снилсу чела, по пути считая подавших согласие
# как найдёт, вернет массив из 2х чисел, место и количество мест
# место - количество подавших согласий перед этим снилсом, включая его
# можно лучше, но работает как надо
def get_places(snils, direction):
    snils = snils.split()
    filename = f'{direction}.pdf'
    raw = parser.from_file(filename)
    kcpcount = raw.count("КЦП")
    text = raw['content'].split('\n')
    kcp = 0
    c = 0
    mest = 173
    for row in text:
        splitted_row = row.split()
        if kcp < kcpcount:
            if "КЦП" in row:
                kcp += 1
            if kcp == kcpcount:
                splitted_row = [int(i) for i in splitted_row if i.isdigit()]
                mest = max(splitted_row)
            continue
        if len(splitted_row) < 3:
            continue
        if direction in splitted_row[-1]:
            c += 1
        if snils[0] == splitted_row[1] and snils[1] == splitted_row[2]:
            return c, mest
    return 0, 0


class Abitur:
    all_dirs = []

    def __init__(self, name: str, snils: str, dirs: tuple, vk_id: int):
        self.name = name
        self.snils = snils
        self.dirs = dirs
        self.last = [(0, 0) for _ in range(len(dirs))]
        self.vk_id = vk_id
        for dir in self.dirs:
            if dir not in Abitur.all_dirs:
                Abitur.all_dirs.append(dir)

    # Проверяет на наличие изменений в местах, и если они есть, то присылает сообщение
    def check(self):
        cur = [get_places(self.snils, direction) for direction in self.dirs]
        if cur != self.last:
            msg = f'Бауманка: Изменения\n'
            for i in range(len(self.dirs)):
                if cur[i] != self.last[i]:
                    msg += f'{self.dirs[i]}: {cur[i][0]}/{cur[i][1]}\n'
            self.last = cur
            self.send_msg(msg)

    # Отправить сообщение вк
    def send_msg(self, msg):
        vk.messages.send(
            user_id=self.vk_id,
            random_id=get_random_id(),
            message=msg
        )
        print(f"{self.name}: {msg}")


if __name__ == '__main__':
    abiturs = [  # обязательно из цифр
        Abitur("Имя", 'Снилс, например: 246-343-410 24', ('09.03.01', "Направления кортежем"), int("id v vk")),
        Abitur("Имя", 'Снилс, например: 246-343-410 24', ('09.03.01', "Направления кортежем"), int("id v vk")),
    ]
    for abitur in abiturs:
        abitur.send_msg("Бауманка Перезапуск\n\n")  # стартовое сообщение при запуске скрипта
    while True:
        def m():
            try:
                get_pdfs(Abitur.all_dirs)
                for abitur in abiturs:
                    abitur.check()
            except Exception as ex:
                # плохая практика, но так можно понять, что возможно проблема со списками
                print("что-то пошло не так", ex)
                m()
        m()
