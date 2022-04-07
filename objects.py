from settings import *


class User:
    def __init__(self):
        self.first_name = ""
        self.phone_number = -1
        self.dir = HOME_DIR
        self.role = "customer"
        self.cart = dict()
        self.user_id = 0


class Vertex:
    # good_id = 0 <=> это папка
    # good_id - id товара в базе данных
    def __init__(self, name, number, parent, good_id=0, descr="", price=0):
        self.number = number
        self.parent = parent
        self.name = name

        self.good_id = good_id
        self.good_description = descr
        self.is_good = good_id != 0
        self.price = price
