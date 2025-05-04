"""
MultipleChoice generator
University: VUT Brno
Faculty: FEKT
File name: MultipleChoice.py
Author: Bc. Václav Pastušek
Creation date: 2022/23
Last update: 12.5.2023
Python Version: 3.8+
"""

# import standard libraries
try:
    import sys
    import random as rn
    import time as tim
    import difflib
    import re
except ModuleNotFoundError as e:
    e.msg += """.\nBe careful, this module is standard and
should not be missing.
I recommend reinstalling Python."""

FILEPATH = "Basic-programator.txt"
RESET = False  # reset all points, correct, gain (Resets over a given range)
RANGE = False  # True -> range(start, stop) / False -> range(0, 10^9)
DUPCONTROL = False  # True -> checking each question with every other
SLOWDEGREASEPOINTS = True  # every round take down -0.1 for question with 1+ points
BOOST = True  # gain boost when you reach some points


def get_new_data():
    with open(FILEPATH, encoding="utf8") as f:
        lines = f.readlines()
    f.close()

    range_start = 0
    range_stop = 10 ** 9

    data = []  # [[line index, question, [answers, bool], coment, points, correct, gain],...]
    quest_flag = False
    quest_line = ""
    for index, line in enumerate(lines):
        if line.startswith("#"):  # skip comments
            continue

        if line.endswith("\\\n"):  # bigger question, adding
            quest_line += line[:-2] + "\n"
            continue

        line_without_spaces = "".join(line.split())
        if not line_without_spaces:  # skip empty line
            quest_flag = False if quest_flag else quest_flag
            quest_line = ""
            continue

        line = line[:-1] if "\n" in line else line  # destroy \n
        if "?" in line and not line.startswith("-"):
            if line.count("?") > 1:
                print("Chyba na řádku:", index + 1, ", u otázky použijte jen 1 \"?\"")
                sys.exit(2)
            else:
                if quest_flag:
                    print("Chyba na řádku:", index + 1, ", předchozí otázka nemá odpovědi")
                    print(":" + quest_line + ":")
                    sys.exit(2)
                else:  # is a question
                    quest_flag = True
                    quest_line += line
                    question, after_question = quest_line.split("?")
                    data_split = after_question.split(":")
                    points = correct = 0.0
                    gain = 0.1
                    if len(data_split) > 1:
                        if isfloat(data_split[1]):
                            points = float(data_split[1])
                        else:
                            print("Chyba na řádku:", index + 1, "body nejsou float")
                            sys.exit(2)

                    if len(data_split) > 2:
                        if isfloat(data_split[2]):
                            correct = float(data_split[2])
                        else:
                            print("Chyba na řádku:", index + 1, "správnost není float")
                            sys.exit(2)

                    if len(data_split) > 3:
                        if isfloat(data_split[3]):
                            gain = float(data_split[3])
                        else:
                            print("Chyba na řádku:", index + 1, "zisk není float")
                            print(gain, data_split)
                            sys.exit(2)

                    data += [[index + 1, question + "?", [], "", points, correct, gain]]

        else:  # answers or inner comment
            if line.startswith("-"):  # inner comment
                data[-1][3] += line[1:] + "\n"
            else:
                if line.endswith(":1"):  # correct answer
                    data[-1][2] += [[line[:-2], True]]
                else:  # incorrect answer
                    data[-1][2] += [[line, False]]

    len_data = len(data)
    range_stop = len_data - 1 if range_stop > len_data - 1 else range_stop
    range_start = len_data - 1 if range_start > len_data - 1 else range_start

    data = sorted(data[range_start:range_stop + 1], key=lambda x: float(x[4]))
    return data


def evaluation_part(lines, answers, guessed_numbers, Q_data, i, start_part):
    correct = 0
    incorrect = 0
    incorrect_list = []
    ans_macro: int = 0
    guess_macro = 0
    answers.reverse()  # otočí odpovědi

    # optimalizace bitovou maskou, protože mě nenapadlo, jak to udělat normálně XD
    for answer in answers:
        ans_macro <<= 1
        if answer[2]:
            ans_macro += 1

    answers.reverse()  # otočí odpovědi

    for guess_num in guessed_numbers:
        if guess_num in "abcdef":
            guess_num = ord(guess_num) - ord("a") + 10
        guess_macro += (1 << int(guess_num))

    comp_macro = ans_macro ^ guess_macro

    for j in range(10 + 26):
        if comp_macro % 2 == 1:
            incorrect += 1
            if j < len(answers):
                if not answers[j][2]:
                    incorrect_list += [j]
            else:
                incorrect_list += [j]
        else:
            if j < len(answers):
                correct += 1
        comp_macro >>= 1

    if not incorrect:
        print("Vše OK.")
    else:
        print("Špatně:", incorrect_list)
        correct_list = [elem[0] for elem in answers if elem[2]]
        print("Správně jsou:", correct_list)

    if Q_data[i][3]:
        print("poznámka:", Q_data[i][3])

    old_points = float(Q_data[i][4])
    succes = float(Q_data[i][5])
    old_gain = gain = float(Q_data[i][6])

    if not incorrect:
        succes += 1
        gain += gain * succes
    else:
        corr_to_incorr = correct / (correct + incorrect)  # x/(x+y)=<0;1>
        # print(correct, incorrect, corr_to_incorr)
        if corr_to_incorr / (len(answers) - 1) >= 0.5:
            succes += 1
            gain += corr_to_incorr * gain * succes
        else:
            succes -= 1
            gain = -gain * (1 - corr_to_incorr)

    lines[Q_data[i][0] - 1] = lines[Q_data[i][0] - 1].split("?")[0] + \
                              ':'.join(["?", str(old_points + gain), str(succes), str(old_gain)]) + \
                              "\n"

    print("Čas úlohy:", round(tim.perf_counter() - start_part, 2), "s")
    print()

    return lines


def repeat_it(text, not_need_zero=False, answer=False, answer_parts=None):
    """
    Repeat input until I am satisfied.
    :param answer:
    :param answer_parts:
    :param text: text
    :param not_need_zero: True/False
    :return: int
    """
    if answer_parts is None:
        answer_parts = []
    while True:  # nekonečná smyčka
        try:
            inp_control: str = input(text).lower()
            if inp_control in ["q", "x"]:  # ukončení
                break
            elif not_need_zero and inp_control == "0":
                var = 1 / 0  # 1000 IQ a přitom lepší než GOTO XD
            else:
                if not answer:
                    if inp_control.isdigit():
                        if int(inp_control) < 0:
                            var = 1 / 0  # -999 IQ
                        return int(inp_control)
                    else:
                        var = 1 / 0  # 420 IQ

                else:
                    char_list = ""
                    if not inp_control:
                        var = 1 / 0

                    for char in inp_control:
                        if char not in "0123456789qwertzuiopasdfghjklyxcvbnm":
                            var = 1 / 0
                        if char not in char_list:
                            char_list += char
                    if char_list == inp_control:
                        return inp_control
                    else:
                        var = 1 / 0  # 69 IQ

        except (SyntaxError, ZeroDivisionError):
            if answer and inp_control:
                print("čísla se opakují")
            print("zadej to znovu nebo x or q pro ukončení")

    if answer:
        lines = answer_parts[0]
        start = answer_parts[1]
        loop_num: object = answer_parts[2]
        data = answer_parts[3]

        # write and close file
        f = open(FILEPATH, 'w', encoding="utf8")  # open file for write
        f.write("".join(lines))
        f.close()

    data = get_new_data()
    count0 = count1 = count2 = count3 = 0
    len_data = len(data)
    for elem in data:
        if float(elem[4]) < 0:
            count0 += 1
        if float(elem[4]) >= 2:
            count1 += 1
        if float(elem[4]) >= 4:
            count2 += 1
        if float(elem[4]) >= 6:
            count3 += 1
    print()
    print("Špatně naučeno(<0):", round(100 * count0 / len_data, 2), "%")
    print("Dobře naučeno(2+):", round(100 * count1 / len_data, 2), "%")
    print("Lépe naučeno(4+):", round(100 * count2 / len_data, 2), "%")
    print("Výborně naučeno(6+):", round(100 * count3 / len_data, 2), "%")

    if answer:
        full_time = round(tim.perf_counter() - start, 2)
        m, s = divmod(full_time, 60)
        h, m = divmod(m, 60)
        h, m = int(h), int(m)
        print("Celkový čas:", f'{h}:{m}:{s:2}', "h:m:s")
        print("Průměrný čas na úlohu:", round(full_time / loop_num, 2), "s")

    data.sort(key=lambda x: x[4])
    print("\nTop 10 špatně naučených otázek[číslo, body, úspěšnost, otázka]:")
    # bad = [(elem[1].split()[0] if re.match(r'^[0-9]+[.)]?$', elem[1]) else "X",
    #         round(float(elem[4]), 2), round(float(elem[5]), 2),
    #         " ".join(elem[1].split()[1:8] + ["..."] if len(elem[1].split()[1:9])
    #                                                    == 8 else elem[1].split()[1:8])   ) for elem in data]

    bad = []
    for elem in data:
        # První prvek: kontrola, zda elem[1] začíná číslem a končí tečkou nebo závorkou
        first_item = "X"

        if elem[1] and re.match(r'^[0-9]+[.)]?$', elem[1].split()[0]):
            first_item = elem[1].split()[0]

        # Druhý a třetí prvek: zaokrouhlení čísel z elem[4] a elem[5] na 2 desetinná místa
        second_item = round(float(elem[4]), 2)
        third_item = round(float(elem[5]), 2)

        # Čtvrtý prvek: zpracování slov z elem[1]
        if first_item == "X":
            # Pokud je first_item "X", vezmeme slova od indexu 0
            words = elem[1].split()[:7]  # Vezmeme slova od indexu 0 do 6 (max 7 slov)
        else:
            # Jinak vezmeme slova od indexu 1 do 7
            words = elem[1].split()[1:8]  # Vezmeme slova od indexu 1 do 7 (max 7 slov)

        # Pokud je v rozsahu 1:9 přesně 8 slov, přidáme "..."
        if len(elem[1].split()[1:9]) == 8:
            words.append("...")

        fourth_item = " ".join(words)

        # Přidání n-tice do výsledného seznamu
        bad.append((first_item, second_item, third_item, fourth_item))

    for i in range(10):
        print(" " if len(bad[i][0]) == 2 else "", end="")
        print(" ".join(str(elem) for elem in bad[i]))

    print("\nTop 10 dobře naučených otázek[číslo, body, úspěšnost, otázka]:")
    for i in range(10):
        print(" " if len(bad[-i - 1][0]) == 2 else "", end="")
        print(" ".join(str(elem) for elem in bad[-i - 1]))

    print("\nUkončil(a) jsi program, progres je na 99,99% uložen.")
    sys.exit(0)


def isfloat(num):
    """
    Control if number is float.
    param num: number
    :return: Bool
    """
    try:
        float(num)
        return True
    except ValueError:
        return False


def duplicates(data):
    """
    Control duplicates questions and answers.
    :param data: data
    :return: None
    """
    questions = [elem[1] for elem in data]
    len_questions = len(questions)
    similar_question = []
    if len_questions > 1:
        for i in range(len(questions)):
            for j in range(i + 1, len(questions)):
                match = difflib.SequenceMatcher(None, questions[i], questions[j]).ratio()
                if match > 0.87:
                    similar_question += ["Shodná otázka(87+%) na řádcích: " + \
                                         str(data[i][0]) + " a " + \
                                         str(data[j][0]) + ", shoda je na " + \
                                         "{:.2f}".format(match * 100) + "%, " + \
                                         "otázky číslo " + str(i + 1) + " a " + str(j + 1)
                                         ]
    if similar_question:
        for elem in similar_question:
            print(elem)
        sys.exit(2)


def pymain():
    print("""
Vítejte v alfa verzi programu MultipleChoice generator
- varování: zálohujte si textový soubor s daty, nicméně data se vždy rychle
    zavírají a nemělo by dojít k smazání dat
- doporučení: program jde kdykoliv ukončit napsáním a potvrzením 'x' nebo 'q',
        při porovnávání duplicitních otázek může trvat pár sekund XD
        odpovědi pište bez mezer jako čísla, př: 069753
""")
    with open(FILEPATH, encoding="utf8") as f:
        lines = f.readlines()
    f.close()

    # počet kol
    loop_num = repeat_it("počet kol(1+)[best 10,20,50,100,500]: ", True)
    if RANGE:
        range_start = repeat_it("rozsah od[indexace od 0!]: ")
        range_stop = repeat_it("rozsah do: ")
        if range_stop < range_start:
            range_stop = range_start
            print("chyba v rozsahu, range_stop bude nastaven na range_start")
    else:
        range_start = 0
        range_stop = 10 ** 9

    print()
    data = []  # [[line index, question, [answers, bool], coment, points, correct, gain],...]
    quest_flag = False
    quest_line = ""
    for index, line in enumerate(lines):
        if line.startswith("#"):  # skip comments
            continue

        if line.endswith("\\\n"):  # bigger question, adding
            quest_line += line[:-2] + "\n"
            continue

        line_without_spaces = "".join(line.split())
        if not line_without_spaces:  # skip empty line
            quest_flag = False if quest_flag else quest_flag
            quest_line = ""
            continue

        line = line[:-1] if "\n" in line else line  # destroy \n
        if "?" in line and not line.startswith("-"):
            if line.count("?") > 1:
                print("Chyba na řádku:", index + 1, ", u otázky použijte jen 1 \"?\"")
                sys.exit(2)
            else:
                if quest_flag:
                    print("Chyba na řádku:", index + 1, ", předchozí otázka nemá odpovědi")
                    print(":" + quest_line + ":")
                    sys.exit(2)
                else:  # is a question
                    quest_flag = True
                    quest_line += line
                    question, after_question = quest_line.split("?")
                    data_split = after_question.split(":")
                    points = correct = 0.0
                    gain = 0.1
                    if len(data_split) > 1:
                        if isfloat(data_split[1]):
                            points = float(data_split[1])
                        else:
                            print("Chyba na řádku:", index + 1, "body nejsou float")
                            sys.exit(2)

                    if len(data_split) > 2:
                        if isfloat(data_split[2]):
                            correct = float(data_split[2])
                        else:
                            print("Chyba na řádku:", index + 1, "správnost není float")
                            sys.exit(2)

                    if len(data_split) > 3:
                        if isfloat(data_split[3]):
                            gain = float(data_split[3])
                        else:
                            print("Chyba na řádku:", index + 1, "zisk není float")
                            print(gain, data_split)
                            sys.exit(2)

                    data += [[index + 1, question + "?", [], "", points, correct, gain]]

        else:  # answers or inner comment
            if line.startswith("-"):  # inner comment
                data[-1][3] += line[1:] + "\n"
            else:
                if line.endswith(":1"):  # correct answer
                    data[-1][2] += [[line[:-2], True]]
                else:  # incorrect answer
                    data[-1][2] += [[line, False]]

        # if index == 20: break

    len_data = len(data)
    range_stop = len_data - 1 if range_stop > len_data - 1 else range_stop
    range_start = len_data - 1 if range_start > len_data - 1 else range_start

    data = sorted(data[range_start:range_stop + 1], key=lambda x: float(x[4]))

    # duplicite controll
    if DUPCONTROL:
        duplicates(data)

    # RESET
    if RESET:
        f = open(FILEPATH, 'w', encoding="utf8")  # open file for write
        for question in data:
            lines[question[0] - 1] = lines[question[0] - 1].split("?")[0] + "?:0.0:0.0:0.1\n"

        f.write("".join(lines))
        f.close()
        print("Byl proveden reset všech bodů, úspěšnosti a přírůstku bodů.")
        print("Pro vypnutí resetu změnte RESET = False.")
        print("Pozor, resetuje jen nad daným rozsahem! -> možné vypnout range")
        sys.exit(5)

    if SLOWDEGREASEPOINTS:
        f = open(FILEPATH, 'w', encoding="utf8")  # open file for write
        for question in data:
            before_quest, after_quest = lines[question[0] - 1].split("?")
            splitted_points = after_quest.split(":")
            if len(splitted_points) > 1:
                points = float(splitted_points[1])
                if points > 1:
                    splitted_points[1] = str(points - 0.1)
                    after_quest = ":".join(splitted_points)
                    lines[question[0] - 1] = "?".join([before_quest, after_quest])

        f.write("".join(lines))
        f.close()

    if BOOST:
        f = open(FILEPATH, 'w', encoding="utf8")  # open file for write
        for question in data:
            before_quest, after_quest = lines[question[0] - 1].split("?")
            splitted_points = after_quest.split(":")
            if len(splitted_points) > 1:
                points = float(splitted_points[1])
                gain = float(splitted_points[3])
                if points > 2:
                    splitted_points[3] = str(0.2)
                if points > 4:
                    splitted_points[3] = str(0.3)
                if points > 6:
                    splitted_points[3] = str(0.5)
                if points > 2:
                    splitted_points[3] += "\n"
                    after_quest = ":".join(splitted_points)
                    lines[question[0] - 1] = "?".join([before_quest, after_quest])

        f.write("".join(lines))
        f.close()

    points_weight = []
    for elem in data:
        if float(elem[4]) < 2:
            points_weight += [float(elem[4])]
        elif float(elem[4]) < 4:
            points_weight += [float(elem[4]) + 1e3]
        elif float(elem[4]) < 6:
            points_weight += [float(elem[4]) + 1e6]
        else:
            points_weight += [float(elem[4]) + 1e9]

    # weight generator
    Q_data = rn.choices(
        population=data,
        # x <= (-x+1+max(body))**2
        weights=list(map(lambda x: (-x + 1 + max(points_weight)) ** 2,
                         points_weight)),

        k=loop_num
    )

    # START
    start = tim.perf_counter()
    for i in range(loop_num):
        start_part = tim.perf_counter()
        # print question
        print(str(i + 1) + "/" + str(loop_num) + ")", Q_data[i][1])

        answers = Q_data[i][2]
        # shuffle answers
        rn.shuffle(answers)
        # [[index, answer, bool],...]
        answers = [[index] + answers[index] for index in range(len(answers))]
        # print("odpovědi", answers)

        # print all answers
        for j, answer in enumerate(answers):
            if j > 9:
                j = chr(j - 10 + ord("a"))
            print(str(j) + ")", answer[1])

        guessed_numbers = repeat_it("Vyber správné čísla/písmena(0-9a-z): ",
                                    False, True, [lines, start, loop_num, data])

        ###################################################################
        # evaluation part
        lines = evaluation_part(lines, answers, guessed_numbers, Q_data, i, start_part)

    # write and cloes file
    f = open(FILEPATH, 'w', encoding="utf8")  # open file for write
    f.write("".join(lines))
    f.close()

    data = get_new_data()

    count0 = count1 = count2 = count3 = 0
    len_data = len(data)
    for elem in data:
        if float(elem[4]) < 0:
            count0 += 1
        if float(elem[4]) >= 2:
            count1 += 1
        if float(elem[4]) >= 4:
            count2 += 1
        if float(elem[4]) >= 6:
            count3 += 1
    print("Špatně naučeno(<0):", round(100 * count0 / len_data, 2), "%")
    print("Dobře naučeno(2+):", round(100 * count1 / len_data, 2), "%")
    print("Lépe naučeno(4+):", round(100 * count2 / len_data, 2), "%")
    print("Výborně naučeno(6+):", round(100 * count3 / len_data, 2), "%")

    full_time = round(tim.perf_counter() - start, 2)
    m, s = divmod(full_time, 60)
    h, m = divmod(m, 60)
    h, m = int(h), int(m)
    print("Celkový čas:", f'{h}:{m}:{s:2}', "h:m:s")
    print("Průměrný čas na úlohu:", round(full_time / loop_num, 2), "s")

    data.sort(key=lambda x: x[4])
    print("\nTop 10 špatně naučených otázek[číslo, body, úspěšnost, otázka]:")
    # bad = [(elem[1].split()[0], round(float(elem[4]), 2), round(float(elem[5]), 2),
    #         " ".join(elem[1].split()[1:8] + ["..."] if len(elem[1].split()[1:9])
    #                                                    == 8 else elem[1].split()[1:8])) for elem in data]

    bad = []
    for elem in data:
        # První prvek: kontrola, zda elem[1] začíná číslem a končí tečkou nebo závorkou
        first_item = "X"

        if elem[1] and re.match(r'^[0-9]+[.)]?$', elem[1].split()[0]):
            first_item = elem[1].split()[0]

        # Druhý a třetí prvek: zaokrouhlení čísel z elem[4] a elem[5] na 2 desetinná místa
        second_item = round(float(elem[4]), 2)
        third_item = round(float(elem[5]), 2)

        # Čtvrtý prvek: zpracování slov z elem[1]
        if first_item == "X":
            # Pokud je first_item "X", vezmeme slova od indexu 0
            words = elem[1].split()[:7]  # Vezmeme slova od indexu 0 do 6 (max 7 slov)
        else:
            # Jinak vezmeme slova od indexu 1 do 7
            words = elem[1].split()[1:8]  # Vezmeme slova od indexu 1 do 7 (max 7 slov)

        # Pokud je v rozsahu 1:9 přesně 8 slov, přidáme "..."
        if len(elem[1].split()[1:9]) == 8:
            words.append("...")

        fourth_item = " ".join(words)

        # Přidání n-tice do výsledného seznamu
        bad.append((first_item, second_item, third_item, fourth_item))

    for i in range(min(10, len(bad))):
        print(" " if len(bad[i][0]) == 2 else "", end="")
        print(" ".join(str(elem) for elem in bad[i]))

    print("\nTop 10 dobře naučených otázek[číslo, body, úspěšnost, otázka]:")
    for i in range(min(10, len(bad))):
        print(" " if len(bad[-i - 1][0]) == 2 else "", end="")
        print(" ".join(str(elem) for elem in bad[-i - 1]))

    sys.exit(0)


if __name__ == "__main__":  # main
    pymain()
