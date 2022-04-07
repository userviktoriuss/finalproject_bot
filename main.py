import telebot
from telebot import types
from objects import *
from settings import *
from collections import deque
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import sqlite3

bot = telebot.TeleBot(TOKEN)

start_shopping_markup = types.ReplyKeyboardMarkup()
start_shopping_button = types.KeyboardButton("Перейти к каталогу")
start_shopping_markup.add(start_shopping_button)

# user_data = dict()
# dirs = dict()
# dirs[1] = Vertex(name="Главная", number=HOME_DIR, parent=HOME_DIR)

"""
dirs[2] = Vertex(name="Айфоны", number=2, parent=HOME_DIR)
dirs[3] = Vertex(name="Телефоны", number=3, parent=HOME_DIR)
dirs[4] = Vertex(name="iPhone 11", number=4, parent=2)
dirs[5] = Vertex(name="iPhone 12", number=5, parent=2)
dirs[6] = Vertex(name="iPhone 13", number=6, parent=2)
"""
1
###############
# объявляем бд


db = sqlite3.connect(f'{PROJECT_PATH}/databases/databases.db',
                     check_same_thread=False)

cursor = db.cursor()

cursor.execute("SELECT * FROM __dirs")
rows = cursor.fetchall()
mx = rows[0][0]
for e in rows:
    mx = max(mx, e[0])
different_dirs = mx
cursor.execute('SELECT * FROM __dirs WHERE good_id=0')
different_goods = 1 + (len(rows) - len(cursor.fetchall()))
all_orders = 0


# void
def dirs_set(num, vertex):
    info = cursor.execute(f'SELECT * FROM __dirs WHERE number={num}')
    if info.fetchone() is None:
        # такого нет - создадим
        query = f"""INSERT INTO __dirs
         (number, parent, name, good_id, good_description, price, is_good)
          VALUES({vertex.number}, {vertex.parent}, '{vertex.name}', 
          {vertex.good_id}, '{vertex.good_description}', 
          {vertex.price}, {vertex.is_good})"""
        cursor.execute(query)
        db.commit()
    else:
        # такой уже есть - обновим
        query = f"""
        UPDATE __dirs
        SET 
        number = {vertex.number},
        parent = {vertex.parent},
        name = '{vertex.name}',
        good_id = {vertex.good_id},
        good_description = '{vertex.good_description}',
        price = {vertex.price},
        is_good = {vertex.is_good} 
        WHERE number = {vertex.number}
        """
        cursor.execute(query)
        db.commit()


# vertex
def dirs_get(num):
    query = f"""
    SELECT * FROM __dirs
    WHERE number = {num}
    """
    cursor.execute(query)
    a = list(cursor.fetchone())
    for i in range(len(a)):
        if a[i] == None:
            a[i] = ''
    return Vertex(number=a[0], parent=a[1], name=a[2], good_id=a[3], descr=a[4], price=a[5])


# void
def dirs_update_column(where, where_val, new_val):
    # def dirs_update_parameter(where, where_val, new_val):
    query = f"""
    UPDATE __dirs
    SET {where} = {new_val}
    WHERE {where} = {where_val}
    """
    cursor.execute(query)
    db.commit()


# void
def dirs_remove(num):
    query = f"""
    DELETE FROM __dirs
    WHERE number = {num}
    """
    cursor.execute(query)
    db.commit()


# mass <vertex>
def dirs_get_by_parameter(where, where_val):
    q = "'" * (type(where_val) == str)
    query = f"""
    SELECT * FROM __dirs
    WHERE {where} = {q}{where_val}{q}
    """

    cursor.execute(query)
    ans = []

    for e1 in cursor.fetchall():
        e = list(e1)
        v = Vertex(number=e[0], parent=e[1], name=e[2], good_id=e[3], descr=e[4], price=e[5])
        ans.append(v)
    return ans


###############################################
# db queries for user_data

# assistive functions
def make_cart(s):
    if s == '':
        return dict()

    s = (s.strip()).split()
    cart = dict()

    for i in range(0, len(s), 2):
        cart[int(s[i])] = int(s[i + 1])
    return cart


def make_string_of_cart(cart):
    s = str(cart).replace('{', '')
    s = s.replace('}', '')
    s = s.replace(',', '')
    s = s.replace(':', '')
    return s


# main part

# user
def user_data_get(id):
    query = f"""
    SELECT * FROM __user_data
    WHERE user_id = {id}
    """

    cursor.execute(query)
    a = list(cursor.fetchone())
    for i in range(len(a)):
        if a[i] == None:
            a[i] = ''

    usr = User()
    usr.user_id = a[0]
    usr.first_name = a[1]
    usr.phone_number = a[2]
    usr.dir = a[3]
    usr.role = a[4]
    usr.cart = make_cart(a[5])

    return usr


# bool
def user_data_consist_id(id):
    info = cursor.execute(f'SELECT * FROM __user_data WHERE user_id={id}')
    if info.fetchone() is None:
        return 0
    return 1


# void
def user_data_set(id, usr):
    if user_data_consist_id(id):
        query = f"""
        UPDATE __user_data
        SET first_name = '{usr.first_name}',
        phone_number = '{usr.phone_number}',
        dir = {usr.dir},
        role = '{usr.role}',
        cart = '{make_string_of_cart(usr.cart)}'
        WHERE user_id = {id}
        """
        cursor.execute(query)
        db.commit()
    else:
        # такого нет - создадим
        query = f"""INSERT INTO __user_data
         (user_id, first_name, phone_number, dir, role, cart)
          VALUES({id}, '{usr.first_name}', {usr.phone_number}, 
          {usr.dir}, '{usr.role}', '{make_string_of_cart(usr.cart)}')"""
        cursor.execute(query)
        db.commit()




###############################################
# возвращает номер созданной вершины
def add_dir(name, parent, good_description=""):
    # все товары и все вершины нумеруются с нуля, чтобы существовал нейтральный элемент 0
    global different_dirs, different_goods

    num = different_dirs + 1
    different_dirs += 1
    good_id = 0

    # является товаром
    if len(good_description):
        good_id = different_goods
        different_goods += 1

    dir = Vertex(name=name, number=num, parent=parent, good_id=good_id, descr=good_description)
    dirs_set(num, dir)
    return num


def rename_dir(number, new_name):
    dir = dirs_get(number)
    dir.name = new_name
    dirs_set(number, dir)


# часть функционала не дописана, так как её проще реализовать с БД
def delete_dir(number, save_children=False):
    if save_children:
        dirs_update_column(where='parent', where_val=number, new_val=dirs_get(number).parent)
        dirs_remove(number)
    else:
        children = deque()
        children.append(number)

        while len(children):
            v = children.popleft()
            # вот тут можно сделать рекурсивный заход в удаление, чтобы вышло очень красиво
            # но я не хочу думать, поэтому пока он будет медленный и не особо лаконичный
            a = dirs_get_by_parameter(where='parent', where_val=v)
            for e in a:
                children.append(e.number)
            dirs_remove(v)


# чисто для проверки

"""
tmp = User()
tmp.first_name = "Виктор"
tmp.phone_number = "8"
tmp.role = "admin"
user_data[845661032] = tmp

tmp = User()
tmp.first_name = "Yarik2040"
tmp.phone_number = "8"
tmp.role = "admin"
user_data[412738021] = tmp
"""


# /чисто для проверки


# admin stuff
@bot.message_handler(commands=["addadmin"])
def add_admin(message):
    user_id = message.chat.id
    # print(user_id)
    if user_data_get(user_id).role != "admin":
        bot.send_message(user_id, f"Только администратор может выполнять эту команду, ваш текущий статус - {user_data_get(user_id).role}")
        return
    text = message.text
    admin_id = text[text.find("admin") + 6:]

    try:
        admin_id = int(admin_id)
    except:
        bot.send_message(user_id, "Введен некорректный id")
    else:
        if user_data_consist_id(admin_id):
            usr = user_data_get(admin_id)
            usr.role = 'admin'
            user_data_set(admin_id, usr)
            bot.send_message(user_id, "Пользователь успешно повышен до администратора")
        else:
            bot.send_message(user_id, "Пользователь не найден")


def add_good_name_step(message):
    user_id = message.chat.id
    text = message.text
    num = add_dir(text, user_data_get(user_id).dir, "Здесь пока что пусто")
    msg = bot.send_message(user_id, "Введите описание товара:")

    usr = user_data_get(user_id)
    usr.dir = num
    user_data_set(user_id, usr)

    bot.register_next_step_handler(msg, add_good_descr_step)
    # если не получится передать вершину, запишем, что пользователь в ней стоит


def add_good_descr_step(message):
    user_id = message.chat.id
    num = user_data_get(user_id).dir
    text = message.text

    dir = dirs_get(num)
    dir.good_description = text
    dirs_set(num, dir)

    # добавить выбор - если пользователь не хочит вводить какую-либо инфу, просто выйти в меню
    msg = bot.send_message(user_id, "Отправьте изображение товара:")
    bot.register_next_step_handler(msg, add_good_picture_step)


def add_good_picture_step(message):
    user_id = message.chat.id
    num = user_data_get(user_id).dir
    # записываем каринку в папку ресурсов. дадим ей номер как в good_id
    fileID = message.photo[-1].file_id
    file = bot.get_file(fileID)
    file_path = file.file_path
    url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'
    urllib.request.urlretrieve(url, f'{PROJECT_PATH}/good_pictures/{dirs_get(num).good_id}.jpg')

    msg = bot.send_message(user_id, "Товар успешно отредактирован.\nВведите 0, чтобы вернуться в каталог.")
    bot.register_next_step_handler(msg, edit_catalogue)


def edit_catalogue_good(message):
    # если мы находимся в товаре, edit_catalogue переведёт выполнение программы сюда
    user_id = message.chat.id
    text = message.text
    num = user_data_get(user_id).dir

    if text == "0":
        usr = user_data_get(user_id)
        usr.dir = dirs_get(user_data_get(user_id).dir).parent
        user_data_set(user_id, usr)

        bot.register_next_step_handler(message, edit_catalogue)
        return

    img = open(f'{PROJECT_PATH}/good_pictures/{dirs_get(num).good_id}.jpg', "rb")
    caption = dirs_get(num).name + "\n" + dirs_get(num).good_description + "\n\nВведите 0, чтобы вернуться"
    msg = bot.send_photo(user_id, img, caption)

    bot.register_next_step_handler(msg, edit_catalogue)


@bot.message_handler(commands=["edit"])
def edit_catalogue(message):
    user_id = message.chat.id
    # print(user_id)
    if user_data_get(user_id).role != "admin":
        msg = bot.send_message(user_id,
            f"Только администратор может выполнять эту команду, ваш текущий статус - {user_data_get(user_id).role}")
        return

    # разбор возвращаемого значения
    text = message.text
    spacecnt = text.count(" ")
    go = ""
    mode = "cd"  # change dir
    new_name = "Без названия"
    # + добавить папку
    # - удалить папку с перепривязкой детей
    # -- удалить и удалить всех всех детей
    # п(или П) <number> <new_name> переименовать папку

    # парсинг и отсеивание неформатных запросов
    if text.replace('/', '') in ['с', 'С', 'c', 'C', 's', 'S']:
        return

    if text.replace('/', '') in ['g', 'G', 'т', 'Т']:
        msg = bot.send_message(user_id, "Введите название товара:")
        bot.register_next_step_handler(msg, add_good_name_step)
        return

    if len(text) > 2 and text[0:2] == "+ ":  # операция +
        mode, go = text[:1], text[2:].strip()
        if len(go) == 0:
            msg = bot.send_message(user_id, "Название директории не может быть пустым!")
            bot.register_next_step_handler(msg, edit_catalogue)
            return
    elif spacecnt == 1:  # операции -, -- на детях
        mode, go = text.split()
        if mode not in ['-', '--']:
            msg = bot.send_message(user_id, "Неправильная команда! Попробуйте снова")
            bot.register_next_step_handler(msg, edit_catalogue)
            return
    elif spacecnt > 1:
        bad = 0
        try:
            mode, go, new_name = text.split(" ", 2)
        except:
            bad = 1

        if mode not in ['п', 'П'] or bad:
            msg = bot.send_message(user_id, "Неправильная команда! Попробуйте снова")
            bot.register_next_step_handler(msg, edit_catalogue)
            return
    else:
        go = text

    if mode != "+" and go != "/edit" and not (mode == 'cd' and go in ['-', '--']):
        try:
            go = int(go)
        except:
            msg = bot.send_message(user_id, "Выберите номер директории или товара\n(в случае ошибки выберите 0)")
            bot.register_next_step_handler(msg, edit_catalogue)
            return
        else:
            if go == 0:
                usr = user_data_get(user_id)
                usr.dir = dirs_get(user_data_get(user_id).dir).parent
                user_data_set(user_id, usr)
            else:
                dirnum = user_data_get(user_id).dir
                mass = dirs_get_by_parameter(where='parent', where_val=dirnum)

                for i in range(len(mass)):
                    mass[i] = mass[i].number

                if len(mass) > 0 and mass[0] == HOME_DIR:
                    mass = mass[1:]
                if 0 < go <= len(mass):
                    if mode == 'cd':
                        usr = user_data_get(user_id)
                        usr.dir = dirs_get(mass[go - 1]).number
                        user_data_set(user_id, usr)
                    elif mode in ['п', 'П']:
                        rename_dir(mass[go - 1], new_name)
                    else:
                        delete_dir(dirs_get(mass[go - 1]).number, mode == '-')
                else:
                    msg = bot.send_message(user_id, "Введите корректный номер.")
                    bot.register_next_step_handler(msg, edit_catalogue)
                    return


    # обработка новой итерации
    dir = dirs_get(user_data_get(user_id).dir)
    dirnum = dir.number

    # специальные запросы администратора
    if mode == '+':
        # добавляем папку и остаёмся в текущей
        add_dir(go, dirnum)
        bot.send_message(user_id, "Новая директория успешно создана.")
        # bot.register_next_step_handler(msg, edit_catalogue)
        # return
    elif mode == 'cd' and go in ['-', '--']:
        # удаляем папку изнутри
        if dirnum != HOME_DIR:
            usr = user_data_get(user_id)
            usr.dir = dirs_get(dirnum).parent
            user_data_set(user_id, usr)

            delete_dir(dirnum, mode == '-')
            bot.send_message(user_id, "Директория успешно удалена.")
        # bot.register_next_step_handler(msg, edit_catalogue)
        # return


    # вывод меню
    # директория могла поменятся; удостоверимся, что это не повлияет
    dir = dirs_get(user_data_get(user_id).dir)
    dirnum = dir.number

    # если находимся в товаре, обработаем его вывод в отдельной функции
    if dirs_get(user_data_get(user_id).dir).good_id != 0:
        edit_catalogue_good(message)
        return

    mass = dirs_get_by_parameter(where='parent', where_val=dirnum)
    for i in range(len(mass)):
        mass[i] = mass[i].number

    # очень удобно было зациклить домашнюю вершину в себя
    # Чтобы она не выводила себя же в список детей, ставим этот костыль
    if len(mass) > 0 and mass[0] == HOME_DIR:
        mass = mass[1:]

    # вывод меню
    menu = ""

    for i in range(len(mass)):
        menu += f"{i + 1}. {dirs_get(mass[i]).name}\n"
    if not menu:
        menu = "Здесь пока ничего нет\n"
    menu = f"{dir.name}:\n" + menu
    menu += "0. Вернуться назад"
    msg = bot.send_message(user_id, menu, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, edit_catalogue)


# admin staff ended


# users stuff
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    msg = None
    print(user_id)
    if not user_data_consist_id(user_id):
        msg = bot.send_message(user_id, """\
Добро пожаловать в наш магазин!
Прежде чем начать покупки, Вам нужно зарегистрироваться
Введите Ваше имя:
""", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name_step)
    else:
        msg = bot.send_message(user_id, f"С возвращением, {user_data_get(user_id).first_name}!", reply_markup=start_shopping_markup)
        bot.register_next_step_handler(msg, process_catalogue_step)


def process_name_step(message):
    user_id = message.chat.id
    name = message.text
    user = User()
    user.first_name = name

    user_data_set(user_id, user)
    msg = bot.send_message(user_id,
        f"Приятно познакомиться, {name}!\nВведите Ваш номер телефона, он может понадобиться для уточнения деталей заказа",
        reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_phone_number_step)


def process_phone_number_step(message):
    user_id = message.chat.id

    usr = user_data_get(user_id)
    usr.phone_number = message.text
    user_data_set(user_id, usr)

    msg = bot.send_message(user_id,
        "Вы успешно зарегистрированы!\nТеперь можно перейти в каталог:",
        reply_markup=start_shopping_markup)
    bot.register_next_step_handler(msg, process_catalogue_step)
    print(user_id)


def process_catalogue_step_good(message):
    # если мы находимся в товаре, process_catalogue переведёт выполнение программы сюда
    user_id = message.chat.id
    text = message.text
    num = user_data_get(user_id).dir

    if text == "0":
        usr = user_data_get(user_id)
        usr.dir = dirs_get(user_data_get(user_id).dir).parent
        user_data_set(user_id, usr)

        bot.register_next_step_handler(message, process_catalogue_step)
        return

    img = open(f'{PROJECT_PATH}/good_pictures/{dirs_get(num).good_id}.jpg', "rb")
    caption = dirs_get(num).name + "\n" + dirs_get(num).good_description + "\n\nВведите 0, чтобы вернуться"
    msg = bot.send_photo(user_id, img, caption)

    bot.register_next_step_handler(msg, process_catalogue_step)


def cart_mass(user_id):
    mass = []
    for e in user_data_get(user_id).cart:
        mass.append((user_data_get(user_id).cart[e], e))
    return mass


def cart_menu(user_id, add_back=1):
    mass = cart_mass(user_id)
    menu = ""

    for i in range(len(mass)):
        menu += f'{i + 1}. {mass[i][0]} шт. {dirs_get(mass[i][1]).name}\n'
    if add_back:
        menu += "0. Вернуться в каталог\n"
        menu += "Оформить заказ - чтобы произвести покупку"
    return menu


def make_order(user_id):
    global all_orders
    # отправляем письмо с деталями заказа на почту

    msg = f'''
user_id: {user_id}
name: {user_data_get(user_id).first_name}
phone_number: {user_data_get(user_id).phone_number}
'''
    msg += cart_menu(user_id, add_back=0)

    all_orders += 1
    msg = MIMEText(msg, 'plain', 'utf-8')
    msg['Subject'] = Header(f'Заказ #{all_orders}', 'utf-8')
    msg['From'] = EMAIL
    msg['To'] = EMAIL

    s = smtplib.SMTP('smtp.mail.ru', 587, timeout=10)
    try:
        s.starttls()
        s.login(EMAIL, EMAIL_PWD)
        s.sendmail(EMAIL, EMAIL, msg.as_string())
    finally:
        s.quit()


def reset(user_id):
    usr = user_data_get(user_id)
    usr.cart = dict()
    usr.dir = HOME_DIR
    user_data_set(user_id, usr)


def process_cart(message):
    user_id = message.chat.id
######################################################################
    text = message.text

    go = text
    # существующие команды
    # 1) вернутья в папашу - 0
    # 2) изменить количество товара
    # 3) купить (оформить заказ)

    if go == 'Оформить заказ':
        make_order(user_id)
        reset(user_id)
        msg = bot.send_message(user_id, "Ваш заказ успешно оформлен.\nНаш оператор перезвонит Вам для уточнения его деталей.\nНажмите на кнопку для перехода в каталог", reply_markup=start_shopping_markup)
        bot.register_next_step_handler(msg, process_catalogue_step)
        return
    elif go == '0':
        msg = bot.send_message(user_id,
                               "Нажмите на кнопку, чтобы вернуться в каталог",
                               reply_markup=start_shopping_markup)
        bot.register_next_step_handler(msg, process_catalogue_step)
        return
    elif go.find(' ') == 1:
        cnt = go[go.find(' ') + 1:]
        go = go[:go.find(' ')]
        try:
            go = int(go)
            mass = cart_mass(user_id)

            if not (1 <= len(mass) <= len(mass)):
                bot.send_message(user_id, 'Неверный номер товара.\nПопробуйте снова')

                menu = cart_menu(user_id)
                msg = bot.send_message(user_id, menu)
                bot.register_next_step_handler(msg, process_cart)
                return
            try:
                cnt = int(cnt)

                usr = user_data_get(user_id)
                usr.cart[mass[go - 1][1]] = cnt
                user_data_set(user_id, usr)

                msg = bot.send_message(user_id, 'Количество товара успешно изменено.')
                #bot.register_next_step_handler(msg, process_cart)
            except:
                msg = bot.send_message(user_id, 'Количество товаров должно быть целым числом')
                #bot.register_next_step_handler(msg, process_cart)
        except:
            msg = bot.send_message(user_id, "Неверный номер товара.\nПопробуйте снова")
            #bot.register_next_step_handler(msg, process_cart)

    menu = cart_menu(user_id)
    msg = bot.send_message(user_id, menu)
    bot.register_next_step_handler(msg, process_cart)


def process_catalogue_step(message):
    user_id = message.chat.id

    # test
    # print(user_data_get(user_id).cart)
    #

    # разбор возвращаемого значения
    go = message.text
    if go.replace('/', '') in ['с', 'С', 'c', 'C', 's', 'S']:
        return

    # переход в корзину
    if go == "Оформить заказ":
        menu = cart_menu(user_id)
        msg = bot.send_message(user_id, menu)
        bot.register_next_step_handler(msg, process_cart)
        return

    # добавление товара в корзину
    if go[0] == '+':
        if go.count(' ') == 2:
            cnt = go[go.rfind(' ') + 1:]
            go = go[go.find(' ') + 1 : go.rfind(' ')]
            mass = dirs_get_by_parameter(where='parent', where_val=user_data_get(user_id).dir)

            for i in range(len(mass)):
                mass[i] = mass[i].number

            if len(mass) > 0 and mass[0] == HOME_DIR:
                mass = mass[1:]
        elif dirs_get(user_data_get(user_id).dir).is_good:
            mass = [user_data_get(user_id).dir]
            # проверим, что есть ровно 1 пробел и cnt != 0
            if go.count(' ') == 1:
                cnt = go[go.find(' ') + 1:]
            else:
                msg = bot.send_message(user_id, "Неправильная команда")
                bot.register_next_step_handler(msg, process_catalogue_step)
                return
            go = 1

        try:
            go = int(go)

            if not 1 <= go <= len(mass):
                msg = bot.send_message(user_id, "Некорректный номер товара")
                bot.register_next_step_handler(msg, process_catalogue_step)
                return
            try:  # это должен быть именно товар
                cnt = int(cnt)
                dir = mass[go - 1]
                if not dirs_get(dir).is_good:
                    msg = bot.send_message(user_id, "В корзину можно класть только товары")
                    bot.register_next_step_handler(msg, process_catalogue_step)
                    return
                if dir not in user_data_get(user_id).cart:
                    usr = user_data_get(user_id)
                    usr.cart[dir] = cnt
                    user_data_set(user_id, usr)
                else:
                    usr = user_data_get(user_id)
                    usr.cart[dir] += cnt
                    user_data_set(user_id, usr)

                msg = bot.send_message(user_id, "Товар успешно добавлен в корзину\nНажмите на кнопку, чтобы вернуться в корзину.",
                                       reply_markup=start_shopping_markup)
                bot.register_next_step_handler(msg, process_catalogue_step)
                return
            except:
                msg = bot.send_message(user_id, "Некорректное количество товара. \nПопробуйте снова")
                bot.register_next_step_handler(msg, process_catalogue_step)
                return
        except:
            msg = bot.send_message(user_id, "Неправильный номер товара, попробуйте снова")
            bot.register_next_step_handler(msg, process_catalogue_step)
            return

    if go != "Перейти к каталогу":
        try:
            go = int(go)
        except:
            msg = bot.send_message(user_id, "Выберите номер директории или товара\n(в случае ошибки выберите 0)")
            bot.register_next_step_handler(msg, process_catalogue_step)
            return
        else:
            if go == 0:
                usr = user_data_get(user_id)
                usr.dir = dirs_get(user_data_get(user_id).dir).parent
                user_data_set(user_id, usr)
            else:
                mass = dirs_get_by_parameter(where='parent', where_val=user_data_get(user_id).dir)

                for i in range(len(mass)):
                    mass[i] = mass[i].number  # питонический треш

                if len(mass) > 0 and mass[0] == HOME_DIR:
                    mass = mass[1:]

                if 0 < go <= len(mass):
                    usr = user_data_get(user_id)
                    usr.dir = dirs_get(mass[go - 1]).number
                    user_data_set(user_id, usr)
                else:
                    msg = bot.send_message(user_id, "Введите коректный номер")
                    bot.register_next_step_handler(msg, process_catalogue_step)
                    return

    # обработка новой итерации
    dir = dirs_get(user_data_get(user_id).dir)

    # если находимся в товаре, обработаем его вывод в отдельной функции
    if dirs_get(user_data_get(user_id).dir).good_id != 0:
        process_catalogue_step_good(message)
        return

    mass = dirs_get_by_parameter(where='parent', where_val=dir.number)
    for i in range(len(mass)):
        mass[i] = mass[i].number
    if len(mass) > 0 and mass[0] == HOME_DIR:
        mass = mass[1:]
    menu = ""

    for i in range(len(mass)):
        menu += f"{i + 1}. {dirs_get(mass[i]).name}\n"
    if not menu:
        menu = "Здесь пока ничего нет\n"
    menu = f"{dir.name}:\n" + menu
    menu += "0. Вернуться назад"
    msg = bot.send_message(user_id, menu, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_catalogue_step)











if __name__ == "__main__":
    bot.polling()

db.close()