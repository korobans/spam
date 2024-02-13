import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit, QTextEdit
import re
import pymorphy2
import csv
from math import exp, log
tags = ['NOUN', 'VERB', 'ADJF']


class SpamFilterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Спам фильтр")
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = QTabWidget()

        # Вкладка "Обучение"
        self.train_tab = QWidget()
        self.tab_widget.addTab(self.train_tab, "Обучение")
        self.init_train_tab()

        # Вкладка "Проверка"
        self.check_tab = QWidget()
        self.tab_widget.addTab(self.check_tab, "Проверка")
        self.init_check_tab()

        self.setCentralWidget(self.tab_widget)

    def init_train_tab(self):
        layout = QVBoxLayout()

        spam_label = QLabel("Это сообщение - спам?")
        layout.addWidget(spam_label)

        self.spam_combobox = QComboBox()
        self.spam_combobox.addItems(["Да", "Нет"])
        layout.addWidget(self.spam_combobox)

        self.text_edit_train = QTextEdit()
        layout.addWidget(self.text_edit_train)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_spam_status)
        layout.addWidget(save_button)

        self.train_tab.setLayout(layout)

    def init_check_tab(self):
        layout = QVBoxLayout()

        self.text_edit_check = QTextEdit()
        layout.addWidget(self.text_edit_check)

        check_button = QPushButton("Проверить")
        check_button.clicked.connect(self.check_spam)
        layout.addWidget(check_button)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        self.check_tab.setLayout(layout)

    def save_spam_status(self):
        selected_value = self.spam_combobox.currentText()
        text = self.text_edit_train.toPlainText()
        cleared_text = self.text_processor(text)
        words = dict()
        for i in cleared_text:
            if i not in words:
                words[i] = 1
            else:
                words[i] += 1
        if selected_value == 'Да':
            data = self.csv_reader('Spam words.csv')

            spam_keys = words.keys()
            for key in data:
                if key in spam_keys:
                    words[key] = data[key] + words[key]
                else:
                    words[key] = data[key]

            self.csv_uploader(words, 'Spam words.csv')
            print(self.csv_reader('Spam words.csv'))
        else:
            data = self.csv_reader('Good words.csv')

            good_keys = words.keys()
            for key in data:
                if key in good_keys:
                    words[key] = data[key] + words[key]
                else:
                    words[key] = data[key]
            self.csv_uploader(words, 'Good words.csv')
        self.text_edit_train.setPlainText('')

    def check_spam(self):
        text = self.text_edit_check.toPlainText()
        cleared_text = self.text_processor(text)

        spam = self.csv_reader('Spam words.csv')
        good = self.csv_reader('Good words.csv')
        spam = self.fit_data(spam)
        good = self.fit_data(good)
        frame = self.data_joiner(good, spam)
        spam_length = self.counter(spam)
        good_length = self.counter(good)
        data = [(word, (frequency[0] + 1) / (good_length + 2), (frequency[1] + 1) / (spam_length + 2)) for
                word, frequency in frame.items()]

        spam_prob = good_prob = 0.0
        for word, prob_if_good, prob_if_spam in data:
            if word in cleared_text:
                spam_prob += log(prob_if_spam)
                good_prob += log(prob_if_good)
            else:
                spam_prob += log(1 - prob_if_spam)
                good_prob += log(1 - prob_if_good)
        e_spam_prob = exp(spam_prob)
        e_good_prob = exp(good_prob)
        self.result_label.setText(f'Вероятность того, что сообщение является спамом: {e_spam_prob/(e_spam_prob + e_good_prob)}')

    def get_clean_word(self, word: str) -> str:
        word = re.sub('[^a-zа-яё-]', '', word, flags=re.IGNORECASE)
        word = word.strip('-')
        return word

    def text_processor(self, text):
        morph = pymorphy2.MorphAnalyzer()
        text = text.split()
        list_clean = [self.get_clean_word(word) for word in text]
        i = 0
        while i != len(list_clean):
            if list_clean[i] == '' or morph.parse(list_clean[i])[0].tag.POS not in tags:
                del list_clean[i]
            else:
                list_clean[i] = morph.parse(list_clean[i])[0].normal_form
                i += 1
        return list_clean

    def csv_uploader(self, text, file):
        keys = list(text.keys())
        values = list(text.values())
        with open(file, 'w', newline='') as csvfile:
            file = csv.writer(csvfile)

            for i in range(len(keys)):
                file.writerow([keys[i], values[i]])

    def csv_reader(self, file):
        spam_data = dict()
        with open(file, newline='') as csvfile:
            file = csv.reader(csvfile, delimiter=',', quotechar='|')

            for row in file:
                spam_data[row[0]] = int(row[1])
        return spam_data

    def fit_data(self, data):
        keys = data.keys()
        bad_keys = []
        for key in keys:
            if int(data[key]) < 3:
                bad_keys.append(key)
        for key in bad_keys:
            del data[key]
        return data

    def data_joiner(self, good, spam):
        df = dict()
        good_keys = good.keys()
        spam_keys = spam.keys()
        for gk in good_keys:
            if gk in spam_keys:
                df[gk] = [good[gk], spam[gk]]
                del spam[gk]
            else:
                df[gk] = [good[gk], 0]
        for i in spam_keys:
            df[i] = [0, spam[i]]
        return df

    def counter(self, data):
        c = 0
        keys = data.keys()
        for key in keys:
            c += data[key]
        return c


def main():
    app = QApplication(sys.argv)
    window = SpamFilterWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()