import sqlite3
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt


class ParameterValueIsWrong(Exception):
    pass


class IdDoesntExistError(Exception):
    pass


class RoastingDegreeDoesntExistError(Exception):
    pass


class GroundAndInGrainsDoesntExistError(Exception):
    pass


class CoffeeTable(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.con = sqlite3.connect('coffee.sqlite')
        self.coffee_info = None
        self.change_form = None
        self.fill_table()
        self.make_or_change_coffee_button.clicked.connect(self.init_change_form)

    def init_change_form(self):
        self.change_form = ChangeForm(self)
        self.change_form.show()
        self.hide()

    def fill_table(self):
        self.get_coffee_info()

        self.coffee_info = self.insert_names_of_properties(self.coffee_info)

        self.coffee_table.setColumnCount(len(self.coffee_info[0]))
        self.coffee_table.setRowCount(len(self.coffee_info))

        for i, row in enumerate(self.coffee_info):
            for j, elem in enumerate(row):
                self.coffee_table.setItem(i, j, QTableWidgetItem(str(row[j])))
                self.coffee_table.item(i, j).setFlags(Qt.ItemIsEditable)

        self.make_header_of_table()

    def get_coffee_info(self):
        cur = self.con.cursor()
        self.coffee_info = cur.execute("""SELECT * FROM Coffee""").fetchall()

    def insert_names_of_properties(self, coffee_info):
        cur = self.con.cursor()
        roasting_degree, ground_or_in_grains = cur.execute("""SELECT name FROM Roasting_degrees""").fetchall(), \
                                               cur.execute("""SELECT name FROM Ground_and_in_grains""").fetchall()

        for i, coffee in enumerate(coffee_info):
            new_coffee = list(coffee)
            new_coffee[2] = roasting_degree[new_coffee[2]][0]
            new_coffee[3] = ground_or_in_grains[new_coffee[3]][0]

            coffee_info[i] = new_coffee

        return coffee_info

    def make_header_of_table(self):
        self.coffee_table.setHorizontalHeaderLabels(('ID', 'Название кофе', 'Степень обжарки', 'Молотый/в зёрнах',
                                                     'Описание вкуса', 'Цена', 'Объём упаковки'))

        header = self.coffee_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

    def closeEvent(self, event):
        self.con.close()


class ChangeForm(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        uic.loadUi('addEditCoffeeForm.ui', self)
        self.con = sqlite3.connect('coffee.sqlite')
        self.make_changes_button.clicked.connect(self.make_changes)

    def make_changes(self):
        try:
            changed_id = self.read_id()
            new_data = self.read_data()

            cur = self.con.cursor()

            if changed_id:
                cur.execute("""UPDATE Coffee
                SET sort_name = ?, roasting_degree = ?, ground_or_in_grains = ?, taste_description = ?, 
                price = ?, volume_of_packet = ?
                WHERE ID = ?""",
                            (new_data[0], new_data[1], new_data[2], new_data[3], new_data[4], new_data[5], changed_id))
            else:
                cur.execute("""INSERT INTO Coffee(sort_name,roasting_degree,ground_or_in_grains,taste_description,
                price,volume_of_packet) VALUES(?, ?, ?, ?, ?, ?)""",
                            (new_data[0], new_data[1], new_data[2], new_data[3], new_data[4], new_data[5]))

            self.con.commit()
            self.error_label.setText('Данные успешно изменены')
        except ParameterValueIsWrong as err:
            self.error_label.setText(f'Ошибка: {err}')

    def read_id(self):
        cur = self.con.cursor()
        changed_id = self.id_input.text()

        if changed_id == '':
            return changed_id

        if not changed_id.isdigit():
            raise ParameterValueIsWrong('введённый id - не число')
        if not (int(changed_id) in map(lambda x: x[0], cur.execute("""SELECT ID FROM Coffee""").fetchall())):
            raise ParameterValueIsWrong('введённый id не существует')

        return changed_id

    def read_data(self):
        sort_name = self.sort_name.text()
        roasting_degree = self.roasting_degree.text()
        ground_or_in_grains = self.ground_or_in_grains.text()
        taste_description = self.taste_description.toPlainText()
        price = self.price.text()
        volume_of_packet = self.volume_of_packet.text()

        self.check_if_correct_roasting_degree(roasting_degree)
        self.check_if_correct_ground_or_in_grains(ground_or_in_grains)
        self.check_if_correct_price(price)
        self.check_if_correct_volume_of_packet(volume_of_packet)

        return sort_name, int(roasting_degree), int(ground_or_in_grains), taste_description, float(price), float(
            volume_of_packet)

    def check_if_correct_roasting_degree(self, roasting_degree):
        cur = self.con.cursor()
        if not roasting_degree.isdigit():
            raise ParameterValueIsWrong('введённая степень обжарки - не число')
        if not (int(roasting_degree) in map(lambda x: x[0],
                                            cur.execute("""SELECT ID FROM Roasting_degrees""").fetchall())):
            raise ParameterValueIsWrong('введённая степень обжарки не существует')

    def check_if_correct_ground_or_in_grains(self, ground_or_in_grains):
        cur = self.con.cursor()
        if not ground_or_in_grains.isdigit():
            raise ParameterValueIsWrong('введённое молотый / в зёрнах - не число')
        if not (int(ground_or_in_grains) in map(lambda x: x[0],
                                                cur.execute("""SELECT ID FROM Ground_and_in_grains""").fetchall())):
            raise ParameterValueIsWrong('введённое молотый / в зёрнах не существует')

    def check_if_correct_price(self, price):
        if self.is_float(price) is None:
            raise ParameterValueIsWrong('введённая цена не число')

    def check_if_correct_volume_of_packet(self, volume_of_packet):
        if self.is_float(volume_of_packet) is None:
            raise ParameterValueIsWrong('введённый объём упаковки не число')

    def is_float(self, n):
        try:
            x = float(n)
            return x
        except ValueError:
            return None

    def closeEvent(self, event):
        self.con.close()
        self.parent.show()
        self.parent.fill_table()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    coffee_table = CoffeeTable()
    coffee_table.show()
    sys.exit(app.exec())
