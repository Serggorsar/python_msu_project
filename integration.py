# реализация Complement Union
from collections import defaultdict
from copy import deepcopy
from sklearn.cluster import MeanShift
import json
import random
import argparse
import codecs


def main():
    parser = argparse.ArgumentParser(description="You can point output files names")
    parser.add_argument("-hse", type=str, default="hse.json", dest='hse_path',
                        help="path to hse teacher's list")
    parser.add_argument("-msu", type=str, default="msu.json", dest='msu_path',
                        help="path to msu teacher's list")
    parser.add_argument("-answer", type=str, default="answer.json", dest='answer_path',
                        help="path to answer file")
    
    args = parser.parse_args()
    # загружаем данные
    hse = json.loads(open(args.hse_path, encoding='utf-8').read())
    msu = json.loads(open(args.msu_path, encoding='utf-8').read())

    rename_columns(hse, 'hse')
    rename_columns(msu, 'msu')

    # все поля
    all_keys = set(msu[0].keys()) | set(hse[0].keys())
    # создаем алфавит, в который входят все символы из встречающихся в именах
    alphabet = list(set(list(''.join(list(map(lambda x: x['name'], hse)) + 
        list(map(lambda x: x['name'], msu))))))
    
    # плохие дяди с вероятностью p могут портить имена: заменять некоторый символ на произвольный из алфавита 
    corrupt_data(hse, alphabet)
    corrupt_data(msu, alphabet)
    
    # имена сотрудников
    hse_names = list(map(lambda x: x['name'], hse))
    msu_names = list(map(lambda x: x['name'], msu))

    hse_dict = get_map(hse)
    msu_dict = get_map(msu)

    num_to_symbol_hse, hse_vectors = get_vectors(hse_names, alphabet)
    num_to_symbol_msu, msu_vectors = get_vectors(msu_names, alphabet)
    vectors = hse_vectors + msu_vectors

    # создаём модель кластеризации и кластеризуем данные из двух векторов
    clustering = MeanShift(bandwidth=1.5).fit(vectors)

    # каждый кластер будет записью в объединенной таблице
    full_table = [{key: None for key in all_keys} for _ in clustering.cluster_centers_]
    for vector, label in zip(vectors, clustering.labels_):
        vector_str = ' '.join(map(str, vector))
        # делаем if не с else, а последовательно, т.к. объединяем поля для Complement Union
        if vector_str in num_to_symbol_hse:
            full_table[label]['name'] = num_to_symbol_hse[vector_str]
            for key, value in hse_dict[num_to_symbol_hse[vector_str]][0].items():
                full_table[label][key] = value

        # если ключи отличаются самую малость (например, ошибка обработки, 
        # доставшаяся из 1 части задания, или вследствие порчи данных плохими дядями),
        # то будем указывать оба, ибо понять какой правильный нетривиально
        if vector_str in num_to_symbol_msu:
            if full_table[label].get('name'):
                if full_table[label]['name'] != num_to_symbol_msu[vector_str]:
                    full_table[label]['name'] += f" ({num_to_symbol_msu[vector_str]})"
            else:
                full_table[label]['name'] = num_to_symbol_msu[vector_str]
            for key, value in msu_dict[num_to_symbol_msu[vector_str]][0].items():
                full_table[label][key] = value

    codecs.open(args.answer_path, 'w', encoding='utf-8').write(json.dumps(full_table, ensure_ascii=False))


def rename_columns(data, university):
    for i in range(len(data)):
        data[i][f'{university}_page_id'] = data[i]['page_id']
        del data[i]['page_id']
        data[i][f'{university}_post'] = data[i]['post']
        del data[i]['post']


def corrupt_data(data, alphabet, p=0.1):
    for i in range(len(data)):
        if random.random() < p:
            pos = random.randint(0, len(data[i]['name']) - 2)
            data[i]['name'] = ''.join([
                data[i]['name'][:pos],
                random.choice(alphabet),
                data[i]['name'][pos + 1:]]
            )


def get_map(data):
    '''возвращает отображение имя -> соответствующие данные о персоне'''
    data_dict = defaultdict(list)
    for hse_line in data:
        without_name = deepcopy(hse_line)
        del without_name['name']
        data_dict[hse_line['name']].append(without_name)
    return data_dict


def to_num(name, alphabet):
    '''получает из строки ее представление в виде вектора частот встречания букв'''
    alphabet_to = {symbol: i for i, symbol in enumerate(alphabet)}
    s = [0 for _ in alphabet]
    for letter in name:
        s[alphabet_to[letter]] += 1
    return s


def get_vectors(names, alphabet):
    '''получает векторизованное представление имён и отображение векторов в слова'''
    num_to_symbol, vectors = {}, []
    for name in names:
        name_num = to_num(name, alphabet)
        vectors.append(name_num)
        num_to_symbol[' '.join(map(str, name_num))] = name
    return num_to_symbol, vectors


'''
Пример выходных данных:
{"name": "Шестимеров АРдрей Алексеевич (Шестимеров Андрей Алексеевич)", 
"msu_post": "М.н.с. кафедры ИИТ", 
"msu_page_id": "/persons/690", 
"phones": ["27269"],
"depart": 
"Факультет компьютерных наук / Департамент больших данных и информационного поиска / Базовая кафедра Яндекс", 
"interests": "", 
"emails": ["ashestimerov@hse.ru", "shestimer@yandex-team.ru", "vrandik@gmail.com"], 
"hse_post": ["Приглашенный преподаватель"], 
"hse_page_id": "/org/persons/134409385"} 
Как видим, объединение устойчиво к небольшой порче данных.
При этом производится "Outer union" и Complementation
'''


if __name__ == "__main__":
    main()
