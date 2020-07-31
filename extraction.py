# Однажды мне стало интересно - сколько человек преподает и на ВМК, и ФКН
# Попробуем ответить на этот вопрос в рамках этой работы
import requests
import re
import json
import codecs
import argparse
import pandas as pd


def levenshtein_distance(a, b):
    "Calculates the Levenshtein distance between a and b. from wikipedia"
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n, m)) space
        a, b = b, a
        n, m = m, n

    current_row = range(n + 1)  # Keep current and previous row, not entire matrix
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]



def get_hse_teachers():
	# сделаем GET-запрос к страничке преподавателей Вышки с фильтром ФКН
	url = 'https://www.hse.ru/org/persons/?ltr=%D0%92%D1%81%D0%B5;udept=120026365'
	r = requests.get(url)

	# как-нибудь обработаем полученный текст, выделяя основные компоненты
	s1 = '<div class="posts persons">' + r.text.split('<div class="posts persons">', 1)[1]
	s1 = s1.split('</div></div></div></div><div class="footer">', 1)[0]

	arr = []
	for idx, s in enumerate(s1.split('</div>\n\n<div class="post person">')):
	    splitted = s.split('<div class="l-extra small">')
	    if len(splitted) > 1:
	        s4, s5 = splitted[1].split('</div>', 1)
	    else:
	        s4 = splitted[0].split('</div>', 1)
	        s4 = s5
	    d = {}
	    # номера телефонов
	    d["phones"] = list(map(lambda s: s[6:][:-7], re.findall(r'<span>.*</span>', s4)))
		# адреса электронной почты
	    emails = list(map(lambda s: s[25:][:-6], re.findall(r'<a class="link" data-at=\'.*\'></a>', s4)))
	    d["emails"] = list(map(lambda r: ''.join(list(map(lambda s: s.replace("-at-", "@"), eval(r)))), emails))
		# ссылка на страницу преподавателя
	    d["page_id"] = re.search(r'(/org/persons/\d*|/staff/\w*)', s5).group(1)
		# его имя
	    d["name"] = re.search(r'title="([\s\w.,\-\(\)]*)"', s5).group(1)
		# должность
	    d["post"] = list(map(lambda x: x.rstrip(":"), re.findall(r'<span>\s*([^<\n\t]*)\s*<', s5)))
		# подразделение
	    d["depart"] = ' / '.join(re.findall(r'<a[^>]*>([^<]*)</a>|</span>', s5.split('class="tag"', 1)[0])).replace('/  /', ';').rstrip("/ ") # "</span>"
	    # интересы
	    try:
	        d["interests"] = ', '.join(re.findall(r'<a[^>]*>([^<]*)</a>', s5.split('class="tag"', 1)[1]))
	    except:
	        d["interests"] = ''
	    # обработка какого-то странного бага, из-за которого запись разрывается на две
	    if len(arr) > 0 and arr[-1]["name"] == d["name"] and arr[-1]["page_id"] == d["page_id"] and \
	            arr[-1]["post"] == d["post"] and arr[-1]["depart"] == d["depart"]:
	        if d["emails"] and d["phones"] and (not arr[-1]["phones"] and not arr[-1]["phones"]):
	            arr[-1]["emails"] = d["emails"]
	            arr[-1]["phones"] = d["phones"]
	        elif arr[-1]["emails"] and arr[-1]["phones"] and (not d["phones"] and not d["phones"]):
	            continue
	    else:
	        arr.append(d)
	    #print(idx, d["name"])
	return arr

def get_msu_teachers():
	arr = []
	for i in range(ord('а'), ord('а')+32):
		# на сайте ВМК страницы с разбиением по буквам
	    url = 'https://cs.msu.ru/persons/all/'+chr(i) 
	    r = requests.get(url)
	    if not r.ok:
	        continue
	    table = r.text[r.text.find('table') : r.text.rfind('table')]
	    table_lines = table.split('</tr>')[:-1]
	    for line in table_lines:
	        d = {}
	        ret = re.search(r'<a href="([\d\w/-]*)">([^<]*)</a>', line)
	        # ссылка на страницу сотрудника
	        d['page_id'] = ret.group(1)
	        # его имя
	        d['name'] = ret.group(2)
	        # и должность
	        try:
	            ret1 = re.search(r'<p>(.*)</p>', line)
	            d['post'] = ''.join([s for idx, s in enumerate(re.split(r'<|>', ret1.group(1))) if idx % 2 == 0])
	        except:
	            try:
	                ret1 = re.search(r'<div>(.*)</div>', line)
	                d['post'] = ''.join([s for idx, s in enumerate(re.split(r'<|>', ret1.group(1))) if idx % 2 == 0])
	            except:
	                d['post'] = ''
	        arr.append(d)
	return arr


if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="You can point output files names")
	parser.add_argument("-hse", type=str, default="hse.json", dest='hse_path',
	                    help="path to msu teacher's list")
	parser.add_argument("-msu", type=str, default="msu.json", dest='msu_path',
	                    help="path to msu teacher's list")
	
	args = parser.parse_args()

	hse_teachers = get_hse_teachers()
	msu_teachers = get_msu_teachers()

	with codecs.open(args.hse_path, 'w', encoding='utf-8') as f:
		f.write(json.dumps(hse_teachers, ensure_ascii=False))

	with codecs.open(args.msu_path, 'w', encoding='utf-8') as f:
		f.write(json.dumps(msu_teachers, ensure_ascii=False))


	# так сколько же пересечений?
	df1, df2 = pd.DataFrame(hse_teachers), pd.DataFrame(msu_teachers)
	# df2['name'] = df2['name'].apply(lambda x: x.strip())
	joined = df1.join(df2.set_index('name'), on='name', how='inner', lsuffix='_hse', rsuffix='_msu')
	print("Общих преподавателей с ФКН и ВМК", len(joined))
	print('\n'.join(list(joined['name'])))
	# На самом деле на ФКН два Черновых Александра Владимировича и один из них - не наш:(

	# А что, если была где-то небольшая опечатка?
	leven3 = []
	for name in hse_teachers:
	    for possib in msu_teachers:
	        if levenshtein_distance(name["name"], possib['name']) < 3:
	            leven3.append('\t\t'.join((name["name"], possib['name'])))
	
	print("\nС расстоянием Левенштейна < 3", len(leven3))
	print('\n'.join(leven3))

	print("\nПомимо Грушо-Глушко добавились три новых абсолютно одинаковых на первый взгляд человека")

	# Их стало больше!!! 
	# А дело все в том, что кто-то криво извлекал имена и они могли заканчиваться на пробелы, как в данном случае
	# строка 134 спасет горе-программистов

	# Как правильно объединить по ключам, которые немного отличаются?
	# ведь мы заранее не знаем, какие еще могут быть ошибки в данных (или в программисте, извлекающем их)
	# узнаем из второго задания...

