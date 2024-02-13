import re
import pymorphy2
import csv
from math import exp, log
tags = ['NOUN', 'VERB', 'ADJF']


def get_clean_word(word: str) -> str:
    word = re.sub('[^a-zа-яё-]', '', word, flags=re.IGNORECASE)
    word = word.strip('-')
    return word


def text_processor(text):
    morph = pymorphy2.MorphAnalyzer()
    text = text.split()
    list_clean = [get_clean_word(word) for word in text]
    i = 0
    while i != len(list_clean):
        if list_clean[i] == '' or morph.parse(list_clean[i])[0].tag.POS not in tags:
            del list_clean[i]
        else:
            list_clean[i] = morph.parse(list_clean[i])[0].normal_form
            i += 1
    return list_clean


def csv_uploader(text, file):
    keys = list(text.keys())
    values = list(text.values())
    with open(file, 'w', newline='') as csvfile:
        file = csv.writer(csvfile)

        for i in range(len(keys)):
            file.writerow([keys[i], values[i]])


def csv_reader(file):
    spam_data = dict()
    with open(file, newline='') as csvfile:
        file = csv.reader(csvfile, delimiter=',', quotechar='|')

        for row in file:
            spam_data[row[0]] = int(row[1])
    return spam_data


def fit_data(data):
    keys = data.keys()
    bad_keys = []
    for key in keys:
        if int(data[key]) < 3:
            bad_keys.append(key)
    for key in bad_keys:
        del data[key]
    return data


def data_joiner(good, spam):
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


def counter(data):
    c = 0
    keys = data.keys()
    for key in keys:
        c += data[key]
    return c


a1 = input('Обучение или проверка?(1/2)\n')
if a1 == '1':
    a2 = input('Является ли сообщение спамом?(Да/Нет)\n')
    print('Введите сообщение')
    text = ''
    text0 = input()
    while text0 != '!':
        text += text0 + ' '
        text0 = input()
    cleared_text = text_processor(text)
    words = dict()
    for i in cleared_text:
        if i not in words:
            words[i] = 1
        else:
            words[i] += 1
    if a2.lower().strip() == 'да':
        data = csv_reader('Spam words.csv')

        spam_keys = words.keys()
        for key in data:
            if key in spam_keys:
                words[key] = data[key] + words[key]
            else:
                words[key] = data[key]

        csv_uploader(words, 'Spam words.csv')
        print(csv_reader('Spam words.csv'))
    else:
        data = csv_reader('Good words.csv')

        good_keys = words.keys()
        for key in data:
            if key in good_keys:
                words[key] = data[key] + words[key]
            else:
                words[key] = data[key]
        csv_uploader(words, 'Good words.csv')
        print(csv_reader('Good words.csv'))
else:
    print('Введите сообщение')
    text = ''
    text0 = input()
    while text0 != '!':
        text += text0 + ' '
        text0 = input()
    cleared_text = text_processor(text)

    spam = csv_reader('Spam words.csv')
    good = csv_reader('Good words.csv')
    spam = fit_data(spam)
    good = fit_data(good)
    frame = data_joiner(good, spam)
    spam_length = counter(spam)
    good_length = counter(good)
    data = [(word, (frequency[0] + 1) / (good_length + 2), (frequency[1] + 1) / (spam_length + 2)) for word, frequency in frame.items()]

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
    print(f'Вероятность того, что сообщение является спамом: {e_spam_prob/(e_spam_prob + e_good_prob)}')
