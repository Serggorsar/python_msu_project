# реализация Complement Union
from collections import defaultdict
from copy import deepcopy
from sklearn.cluster import MeanShift
import json
import random
import argparse
import codecs

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="You can point output files names")
	parser.add_argument("-hse", type=str, default="hse.json", dest='hse_path',
	                    help="path to msu teacher's list")
	parser.add_argument("-msu", type=str, default="msu.json", dest='msu_path',
	                    help="path to msu teacher's list")
	parser.add_argument("-answer", type=str, default="answer.json", dest='answer_path',
	                    help="path to msu teacher's list")
	
	args = parser.parse_args()
	# загружаем данные
	hse = json.loads(open(args.hse_path, encoding='utf-8').read())
	msu = json.loads(open(args.msu_path, encoding='utf-8').read())

	for i in range(len(hse)):
	    hse[i]['hse_page_id'] = hse[i]['page_id']
	    del hse[i]['page_id']
	    hse[i]['hse_post'] = hse[i]['post']
	    del hse[i]['post']
	for i in range(len(msu)):
	    msu[i]['msu_page_id'] = msu[i]['page_id']
	    del msu[i]['page_id']
	    msu[i]['msu_post'] = msu[i]['post']
	    del msu[i]['post']
	# все поля
	all_keys = set(msu[0].keys()) | set(hse[0].keys())
	# создаем алфавит, в который входят все символы из встречающихся в именах
	alphabet = list(set(list(''.join(list(map(lambda x: x['name'], hse))+list(map(lambda x: x['name'], msu))))))
	alphabet_to = {symbol: i for i, symbol in enumerate(alphabet)}
	# плохие дяди с вероятностью p могут портить имена: заменять некоторый символ на произвольный из алфавита 
	p = 0.1
	for i in range(len(hse)):
	    if random.random() < p:
	        pos = random.randint(0, len(hse[i]['name']) - 2)
	        hse[i]['name'] = hse[i]['name'][:pos] + random.choice(alphabet) + hse[i]['name'][pos+1:]
	for i in range(len(msu)):
	    if random.random() < p:
	        pos = random.randint(0, len(hse[i]['name']) - 2)
	        msu[i]['name'] = msu[i]['name'][:pos] + random.choice(alphabet) + msu[i]['name'][pos+1:]
	# имена сотрудников
	hse_names = list(map(lambda x: x['name'], hse))
	msu_names = list(map(lambda x: x['name'], msu))
	# отображение имя -> соответствующие данные о персоне
	hse_dict = defaultdict(list)
	for hse_line in hse:
	    without_name = deepcopy(hse_line)
	    del without_name['name']
	    hse_dict[hse_line['name']].append(without_name)
	    
	msu_dict = defaultdict(list)
	for msu_line in msu:
	    without_name = deepcopy(msu_line)
	    del without_name['name']
	    msu_dict[msu_line['name']].append(without_name)

	# функция, получающая из строки ее представление в виде вектора частот встречания букв
	def to_num(name):
	    s = [0 for _ in alphabet]
	    for x in name:
	        s[alphabet_to[x]] += 1
	    return s

	# получаем векторизованное представление имён, а также отображение векторов в соответствующие слова
	num_to_symbol_hse = {}
	hse_vectors = []
	for name in hse_names:
	    name_num = to_num(name)
	    hse_vectors.append(name_num)
	    num_to_symbol_hse[' '.join(map(str, name_num))] = name

	num_to_symbol_msu = {}
	msu_vectors = []
	for name in msu_names:
	    name_num = to_num(name)
	    msu_vectors.append(name_num)
	    num_to_symbol_msu[' '.join(map(str, name_num))] = name
	    
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
	        cur_dict = hse_dict[num_to_symbol_hse[vector_str]][0]
	        for key in cur_dict:
	            full_table[label][key] = cur_dict[key]
	    # если ключи отличаются самую малость (например, ошибка обработки, 
	    # доставшаяся из 1 части задания, или вследствие порчи данных плохими дядями),
	    # то будем указывать оба, ибо понять какой правивльный нетривиально
	    if vector_str in num_to_symbol_msu:
	        if full_table[label].get('name'):
	            if full_table[label]['name'] != num_to_symbol_msu[vector_str]:
	                full_table[label]['name'] += ' (' + num_to_symbol_msu[vector_str] +  ')'
	        else:
	            full_table[label]['name'] = num_to_symbol_msu[vector_str]
	        cur_dict = msu_dict[num_to_symbol_msu[vector_str]][0]
	        for key in cur_dict:
	            full_table[label][key] = cur_dict[key]

	codecs.open(args.answer_path, 'w', encoding='utf-8').write(json.dumps(full_table, ensure_ascii=False))

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

