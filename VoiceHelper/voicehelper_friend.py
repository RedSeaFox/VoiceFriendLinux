import os.path
# import pathlib
from pathlib import Path
from urllib.parse import unquote
import time
import json
# Нужен микрофон. Для этого можно использовать pyaudio.
# Можно использовать SpeechRecognition, который все равно использует pyaudio.
# PyAudio предоставляет Python связь с PortAudio v19 (кроссплатформенной библиотекой ввода-вывода аудио)
# https://people.csail.mit.edu/hubert/pyaudio/docs/
# https://people.csail.mit.edu/hubert/pyaudio/
import pyaudio
# Linux +
# Были сообщения от ALSA типа "ALSA lib pcm_dmix.c:999:(snd_pcm_dmix_open) unable to open slave"
# и "jack server is not running or cannot be started"
# Помогло решение отсюда https://stackoverflow.com/questions/65079325/problem-with-alsa-in-speech-recognitionpython-3
# Хотя явно sounddevice нигде не используется, но import sounddevice помогает
import sounddevice
# Linux -
# Для распознавания речи используем vosk - автономный API распознавания речи
from vosk import KaldiRecognizer
# Для преобразования текста в речь (для ответов друга) используем pyttsx3
# import pyttsx3
# Linux +
# В Linux используем speechd
import speechd
# Linux -
# Для воспроизведения аудио файлов будем использовать vlc
import vlc

import voicehelper_friend_config as word

CHANNELS = 1  # моно
RATE = 16000  # частота дискретизации - кол-во фреймов в секунду
CHUNK = 8000  # кол-во фреймов за один "запрос" к микрофону - тк читаем по кусочкам
FORMAT = pyaudio.paInt16  # глубина звука = 16 бит = 2 байта

# Для Windows использовала pyttsx3
# Для Linux  rhvoice с speechd
# engine = pyttsx3.init()
client = speechd.SSIPClient('friends_voice')
client.set_output_module('rhvoice')
client.set_language('ru')
client.set_rate(15)
client.set_punctuation(speechd.PunctuationMode.SOME)


# Чтобы использовать PyAudio, сначала создаем экземпляр PyAudio, который получит
# системные ресурсы для PortAudio (короче подключаемся к микрофону)
py_audio = pyaudio.PyAudio()
# Открываем поток для чтения (input=True) данных с микрофона по-умолчанию и задаем параметры
stream = py_audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
rec = KaldiRecognizer(word.MODEL_VOSK, 16000)

# Большинство команд к другу касаются плеера, поэтому он должен быть всегда доступен
vlc_instance = vlc.Instance()
media_list_player = vlc_instance.media_list_player_new()
media_list = vlc_instance.media_list_new()

len_playlist = 0


def read_statuses_from_file():
    # При запуске программы считываем состояние:какой плейлист был текущим на момент закрытия,
    # какой трек и позицию в треке из файла CurrentStatus (word.FILE_STATUS) в каталоге программы
    name_file_status = word.FILE_STATUS
    current_playlist = word.PlAYLIST_BY_DEFAULT
    current_track_index = 0
    current_track_position = 0

    # Считываем данные из json файла
    try:
        with (open(name_file_status, 'r', encoding='utf-8') as file):
            loaded_data = json.load(file)
            print('json файл считан')
            # Получаем последний плейлист
            current_playlist = loaded_data.get("current_playlist", word.PlAYLIST_BY_DEFAULT)
            # current_playlist = loaded_data.get("current_playlist", word.PlAYLIST_BY_DEFAULT)
            print('current_playlist = ', current_playlist)
            # Получаем последний трек
            if current_playlist == word.PlAYLIST_BY_DEFAULT:
                current_track_index = 0
                current_track_position = 0
            else:
                # current_track = loaded_data.get(current_playlist, {})
                # ******************
                dir_name_track = Path(current_playlist)
                print('dir_name_track = ', dir_name_track)
                dir_track = dir_name_track.parent
                print('dir_track = ', dir_track)
                # Надо получить имя плейлиста, а не папки!!!
                # current_playlist_name = dir_track.name
                current_playlist_name = dir_name_track.stem
                print('current_playlist_name = ', current_playlist_name)
                # *****************
                # current_track_index = loaded_data.get(current_playlist.get("track_number",0), 0)
                seek_playlist = loaded_data[current_playlist_name]
                current_track_index = seek_playlist['current_track_index']
                current_track_position = seek_playlist["current_track_position"]
                # ].get(current_playlist.get("track_number",0), 0)
                # current_track_position = loaded_data.get(current_playlist.get("track_position",0), 0)
            print('current_track_index = ',current_track_index, '  current_track_position = ', current_track_position)
    except FileNotFoundError:
        print("FileNotFoundError")
        current_playlist = word.PlAYLIST_BY_DEFAULT
        current_track_index = 0
        current_track_position = 0
        # print('Чтение json. Файл не найден или поврежден. Берем значения по умолчанию')
    except json.JSONDecodeError:
        print('JSONDecodeError')
        current_playlist = word.PlAYLIST_BY_DEFAULT
        current_track_index = 0
        current_track_position = 0
    except Exception as e:
        # Другие возможные ошибки при работе с файлом
        print(f"Произошла другая ошибка: {e}")

    statuses = {"current_playlist": current_playlist, "current_track_index": current_track_index,
                "current_track_position": current_track_position}

    return statuses


def read_statuses_from_track():
    dir_playlist = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST

    media_player = media_list_player.get_media_player()
    # Получаем позицию в текущем треке
    position_in_media = media_player.get_position()
    print('read_statuses_from_track() => media_player.get_position() = ', position_in_media)

    med = media_player.get_media()
    print('media_list_player.get_state() = ', media_list_player.get_state())
    # Получаем индекс текущего трека в плейлисте
    # *************************
    # media_list_player.pause()
    # ******************************
    # media_list.lock()
    index_of_media = media_list.index_of_item(med)
    # media_list.unlock()
    print('read_statuses_from_track() => index_of_media', index_of_media)

    # *************************
    # media_list_player.pause()
    # ******************************
    # Получаем имя текущего плейлиста
    mrl = med.get_mrl()
    decoded_mrl = unquote(mrl)
    dir_name_track = Path(decoded_mrl)
    dir_track = dir_name_track.parent
    current_playlist_name = dir_track.name
    # to do Если программа, то сохранять в каталог с программой

    current_playlist = dir_playlist + '/' + current_playlist_name + '.m3u'

    statuses = {"current_playlist_name": current_playlist_name, "current_playlist": current_playlist,
                "current_track_index": index_of_media, "current_track_position": position_in_media}

    return statuses


def save_current_status():
    name_file_status = word.FILE_STATUS
    dir_playlist = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST

    # Получаем данные закрываемого плейлиста (который сейчас сменим на новый плейлист)
    statuses = read_statuses_from_track()

    # Считываем данные из json файла в loaded_data, добавляем в loaded_data данные закрываемого плейлиста
    # и записываем loaded_data опять в json файл
    try:
        with open(name_file_status, 'r', encoding='utf-8') as file:
            loaded_data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        print('json файла поврежден. Создаем новый пустой json файл')
        loaded_data = {}
    except Exception as e:
        # Другие возможные ошибки при работе с файлом
        print(f"Произошла другая ошибка: {e}")
        loaded_data = {}

    print('loaded_data из файла: ', loaded_data)

    current_playlist = statuses["current_playlist"]
    loaded_data["current_playlist"] = current_playlist

    current_playlist_name = statuses["current_playlist_name"]
    current_track_position = statuses["current_track_position"]

    current_track_index = statuses["current_track_index"]
    if current_track_index < 0:
        current_track_index = 0
        current_track_position = 0

    track_info = {"current_track_index": current_track_index,
                  "current_track_position": current_track_position}
    loaded_data[current_playlist_name] = track_info

    print('loaded_data в файл: ', loaded_data)

    with open(name_file_status, 'w', encoding='utf-8') as file:
        json.dump(loaded_data, file, ensure_ascii=False, indent=4)


# Обрабатывает команду список
def set_playlist(set_commands, result_text):
    # Получаем название каталога с плейлистами из домашней папки
    dir_playlst = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST
    # Проверяем есть ли такой каталог
    if not os.path.isdir(dir_playlst):
        print('Нет каталога с плейлистами. Сообщаем пользователю.')
        say_text(word.DIR_PLAYLIST_NO)
        # Может быть сюда вставить загрузку плейлиста по умолчанию? to do
        return

    # Если каталог есть, то получаем в список все названия файлов из этого каталога
    list_of_file = os.listdir(dir_playlst)
    print('Каталог с плейлистами есть.Список файлов')
    print(list_of_file)

    # Создаем множество, в которое поместим все названия плейлистов из домашней папки
    # Множество, чтобы можно было получить пересечение с заказанным плейлистом
    set_of_playlist = set()
    for file in list_of_file:
        if file.endswith('.m3u'):
            name_playlist = file[:-4]
            set_of_playlist.add(name_playlist)

    # Ищем есть ли названый плейлист в списке плейлистов
    playlist_for_play = set_of_playlist & set_commands

    if len(playlist_for_play) == 0:
        save_current_status()
        # Если названый плейлист не найден в списке плейлистов, то перечисляем все плейлисты, которые есть
        say_text(word.USER_NAME + word.ALL_PLAYLIST_1)
        time.sleep(2)
        for name in set_of_playlist:
            say_text(os.path.splitext(os.path.basename(name))[0])
            time.sleep(0.05)
            # Это чтобы паузы были между названиями

        # И предлагаем выбрать один из них
        say_text(word.USER_NAME + word.ALL_PLAYLIST_2)
    else:
        #  Теперь новый плейлист будет точно загружаться, а значит надо запомнить старый плейлист и позицию в медиа.
        # Сохраняем данные в word.FILE_STATUS
        save_current_status()

        media_list_player.stop()

        new_playlist = list(playlist_for_play)[0]
        play_vlc(new_playlist)

        # to do Если во множестве оказалось несколько плейлистов, то об этом надо сообщить.
        # Пока берем один элемент множества


def load_playlist(playlist_name: str):
    playlist_list = list()

    try:
        playlist_m3u = open(playlist_name, encoding='utf-8')
        playlist_list_from_m3u = playlist_m3u.readlines()

    except FileNotFoundError:
        say_text(word.PLAYLIST_NOT_FOUND)
        return playlist_list

    except Exception:
        say_text(word.PLAYLIST_EXCEPTION)
        return playlist_list

    for line in playlist_list_from_m3u:
        if line[0:5] == '/home':
            # В Windows плейлисты делала в vlc. По умолчанию плейлист сохраняет путь к файлу  в url формате,
            # но в Linux при сохранении плейлиста в vlc url путь с русскими буквами перекодируется в английский.
            # Поэтому для создания плейлиста в Linux использую JuK, а он создает плейлисты с обычными путями.
            # Для определения, что это путь к файлу использую /home
            media_path = os.path.abspath(line.rstrip())
            if os.path.isfile(media_path):
                playlist_list.append(media_path)

    # end_of_list.mp3 нужен, чтобы сообщить пользователю о конце плейлиста и чтобы
    # не попасть в бесконечный цикл, когда "не медиа файл" последний в плейлисте (см. main() media_list_player.next())
    # to do
    # Надо понять как в Linux можно записать озвученный текст в файл с использованием
    # speechd и rhvoice
    # Пока проверку и генерацию файла не делаю, предполагаю что он есть
    # Сами файлы скопировала из Windows
    # if len(playlist_list) > 0:
    #     if not os.path.isfile(word.END_OF_LIST):
    #         engine.save_to_file(word.USER_NAME + word.PLAYLIST_END, word.END_OF_LIST)
    #         engine.runAndWait()
    #
    #     playlist_list.append( word.END_OF_LIST)
    #
    #     if not os.path.isfile(word.START_OF_LIST):
    #         engine.save_to_file(word.USER_NAME + word.PLAYLIST_START, word.START_OF_LIST)
    #         engine.runAndWait()
    #
    #     playlist_list.insert(0,word.START_OF_LIST)
    playlist_list.append(word.END_OF_LIST)
    playlist_list.insert(0, word.START_OF_LIST)

    # # Чтобы избежать дублей в плейлисте
    # to_set = set(playlist_list)
    # playlist_list = list(to_set)

    return playlist_list


def play_vlc(playlist_for_play='Программа.m3u'):
    global len_playlist
    global media_list

    # print('play_vlc() current_playlist = ' + current_playlist)
    # Здесь надо сообщить, какой плейлист загружается
    # current_playlist_name = os.path.splitext(os.path.basename(current_playlist))[0]
    # say_text(word.USER_NAME + word.START_ON_PLAYLIST + current_playlist_name)
    # time.sleep(2)

    # Если плеер уже запущен, но находится в состоянии пауза, то запускаем его (продолжаем играть)
    if media_list_player.get_state() == vlc.State(4) :
        statuses = read_statuses_from_track()
        say_text(word.USER_NAME + word.START_ON_PLAYLIST + statuses["current_playlist_name"])
        time.sleep(2)
        media_list_player.pause()

    #  Если Stopped
    elif media_list_player.get_state() == vlc.State(5) :
        # Получаем название каталога с плейлистами из домашней папки
        dir_playlst = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST
        new_playlist = dir_playlst + '/' + playlist_for_play + '.m3u'
        playlist_list = load_playlist(new_playlist)

        len_playlist = len(playlist_list)

        # if len(playlist_list) == 0:
        if len_playlist == 0:
            say_text(word.PLAYLIST_EMPTY)
            return

        media_list = vlc_instance.media_list_new()

        for song in playlist_list:
            media_list.add_media(song.rstrip())

        media_list_player.set_media_list(media_list)

        print('State(5) ')
        media_list_player.play()

    else:
        # Если плеер еще не запущен - запускаем.
        # При этом создаем новый плейлист и загружаем в него список
        # Плейлист из файла загружаем в список (список, а не кортеж, т.к. планируется добавление в плейлист?)
        # Плейлисты будут хранится в /home/seafox/VoiceFriend_PlayLists/

        statuses = read_statuses_from_file()
        current_playlist_name = Path(statuses["current_playlist"]).stem
        say_text(word.USER_NAME + word.START_ON_PLAYLIST + current_playlist_name)
        time.sleep(2)

        playlist_list = load_playlist(statuses["current_playlist"])

        len_playlist = len(playlist_list)

        # if len(playlist_list) == 0:
        if len_playlist == 0:
            say_text(word.PLAYLIST_EMPTY)
            return

        media_list = vlc_instance.media_list_new()


        for song in playlist_list:
            media_list.add_media(song.rstrip())

        media_list_player.set_media_list(media_list)

        # Получаем из файла данные о текущем треке и текущей позиции.
        # Выбираем трек и позицию в нем для воспроизведения
        media_list_player.play_item_at_index(statuses["current_track_index"])

        media_player = media_list_player.get_media_player()
        media_player.set_position(statuses["current_track_position"])

        # ***********************
        # current_playlist = statuses["current_playlist"]
        # dir_name_track = Path(current_playlist)
        # dir_track = dir_name_track.parent
        # current_playlist_name = dir_track.stem
        # current_playlist_name = Path(statuses["current_playlist"]).stem

        # *******************

        # say_text(word.USER_NAME + word.START_ON_PLAYLIST + current_playlist_name)
        # time.sleep(2)
        print('State else')
        media_list_player.play()

        # Текщую позицию при сохранении получаем так
        # media_player = media_list_player.get_media_player()
        # n = media_player.get_position()
        # print('media_player.get_position() = ', n)
        # Значит устанавливать будем так:
        # media_player.set_position(0.5)
        # media_list_player.play_item_at_index(2)
        # Или так?
        # media_player.set_mrl('/home/seafox/VoiceFriend_Musik/Песни/ABBA - MONEY, MONEY, MONEY.mp3')
        # dev -

#  Вариант с pyttsx3 (engine) использовала в Windows
# def say_text(text):
#     engine.say(text)
#     engine.runAndWait()
# Linux +
def say_text(text):
    text_len = len(text)
    # time_len = text_len / 10 - 5
    time_len = text_len / 10 - 7

    client.speak(text)
    time.sleep(2)

    if time_len > 0:
        time.sleep(time_len)
# Linux -

def result_by_words(result_text):
    result_text = result_text.replace("\n", "")
    result_text = result_text.replace("partial", "")
    result_text = result_text.replace(":", "")
    result_text = result_text.replace("{", "")
    result_text = result_text.replace("}", "")
    result_text = result_text.replace('"', "")

    return result_text.split()


def listen_to_user():
    record_seconds = 2
    listen = True
    max_replay = 1
    count_replay = 0
    max_len_rec = 100
    result_text = ''

    # stream.start_stream() Надо?
    while listen:
        for _ in range(0, RATE // CHUNK * record_seconds):
            data = stream.read(CHUNK)
            rec.AcceptWaveform(data)

        # Проверяем, изменился текст или нет и если не изменился, то сколько раз он уже не менялся
        if result_text == rec.PartialResult():
            count_replay += 1
            # Если текст не меняется уже max_replay раз
            if count_replay > max_replay - 1:
                listen = False
        elif len(rec.PartialResult()) > max_len_rec:
            listen = False
        else:
            count_replay = 0
            result_text = rec.PartialResult()

    print('listen_to_user(): result_tex: ', result_text.replace("\n", ""))

    return result_text


def play_next():
    media_list_player.next()


def play_previous():
    media_list_player.previous()
    time.sleep(1)

    media_player = media_list_player.get_media_player()

    stepping = True

    while stepping:
        # Если воспроизведение еще не началось, то это не медиа файл => переходим еще раз вверх
        if media_player.get_position() == 0:
            media_list_player.previous()
            time.sleep(0.5)
        else:
            stepping = False


def get_number(set_commands, result_text):
    set_number_in_result = set_commands & word.All_NAME_NUMBER

    if not set_number_in_result:
        return 0

    number_in_result = []

    is_thousand = False
    index_thousand = 0
    number_thousand = 0

    is_hundred = False
    index_hundred = 0
    number_hundred = 0

    number = 0

    for w in result_text:
        if w in set_number_in_result:
            number_in_result.append(w)

    for w in word.NAME_THOUSAND:
        if w in number_in_result:
            number_thousand = 1

            index_thousand = number_in_result.index(w)
            thousand = number_in_result[:index_thousand + 1]

            for ww in thousand:
                number_thousand = number_thousand * word.NAME_NUMBER_DICT[ww]

            is_thousand = True
            break

    for w in word.NAME_HUNDRED:
        if w in number_in_result:
            number_hundred = 1

            index_hundred = number_in_result.index(w)

            if is_thousand:
                hundred = number_in_result[index_thousand+1:index_hundred + 1]
            else:
                hundred = number_in_result[:index_hundred + 1]

            for ww in hundred:
                number_hundred = number_hundred * word.NAME_NUMBER_DICT[ww]

            is_hundred = True
            break

    number_residue = number_in_result[:]

    if is_thousand:
        number_residue = number_in_result[index_thousand+1:]

    if is_hundred:
        number_residue = number_in_result[index_hundred+1:]

    for ww in number_residue:
        number = number + word.NAME_NUMBER_DICT[ww]

    number = number_thousand + number_hundred + number

    # todo
    # убрать ограничение 2000
    if number > word.MAX_NUMBER:
        say_text(word.MESSAGE_MAX_NUMBER)
        return 0

    return number

# Переход к треку под указанным номером (например, "трек 3") или
# к указанному времени (например 20 секунд) внутри трека
# Пока распознается только время или в секундах, или в минутах, или в часах.
# То есть время 2 минуты 6 секунд будет распознано как 8 секунд
def go_to(set_commands, result_text):
    number = get_number(set_commands, result_text)
    print('go_to(): number: ', number)

    if not number:
        say_text(word.USER_NAME + word.NO_NUMBER)
        return

    if not set_commands.isdisjoint(word.SET_MEASURE_TRACK):
        if media_list_player.get_state() == vlc.State(0):
            play_vlc()
            media_list_player.set_pause(1)

        if number > len_playlist - 2:
            say_text(word.USER_NAME + word.number_greater_len_pl(number, len_playlist-2))
            return

        say_text(word.USER_NAME + word.GOTO_TRACK + str(number))

        media_list_player.play_item_at_index(number)  # переходит к треку номер number

    elif not set_commands.isdisjoint(word.SET_MEASURE_TIME):
        time_factor = 1

        if not set_commands.isdisjoint(word.SET_MEASURE_SECOND):
            time_factor = 1000
        elif not set_commands.isdisjoint(word.SET_MEASURE_MINUTE):
            time_factor = 60000
        elif not set_commands.isdisjoint(word.SET_MEASURE_HOUR):
            time_factor = 3600000

        media_player = media_list_player.get_media_player()
        media_player.set_time(number * time_factor)

        media_list_player.play()

    else:
        say_text(word.USER_NAME + word.MEASURE_UNDEFINED)


# Быстрая перемотка вперед. Прыжок через несколько треков (например два трека)
# или через несколько секунд/минут/часов (например 20 секунд)
# Пока распознается только время или в секундах, или в минутах, или в часах.
# То есть время 2 минуты 6 секунд будет распознано как 8 секунд
def go_forward(set_commands, result_text):
    number = get_number(set_commands, result_text)

    if not number:
        say_text(word.USER_NAME + word.NO_NUMBER)
        return

    if not set_commands.isdisjoint(word.SET_MEASURE_TRACK):
        if number > word.MAX_JUMP:
            say_text(word.LIMIT_MAX_JUMP)
            return

        if media_list_player.get_state() == vlc.State(0):
            play_vlc()

        for _ in range(number):
            media_list_player.next()
            # todo
            # Возможно вынести время сна в voicehelper_friend_config.py, т.к.
            # на разных компах возможно надо другое время сна
            # time.sleep(0.5)
            time.sleep(0.01)
        # Не нашла ничего другого для перехода на заданное количество треков от ТЕКУЩЕГО трека.
        # А именно, не нашла как определить индекс текущего трека.
        # MediaList.index_of_item не подходит, т.к. ищет первое вхождение, а md в плейлисте может дублироваться
        print('go_forward() by MEASURE_TRACK: number:', number)

    elif not set_commands.isdisjoint(word.SET_MEASURE_TIME):
        time_factor = 1
        if not set_commands.isdisjoint(word.SET_MEASURE_SECOND):
            time_factor = 1000
        elif not set_commands.isdisjoint(word.SET_MEASURE_MINUTE):
            time_factor = 60000
        elif not set_commands.isdisjoint(word.SET_MEASURE_HOUR):
            time_factor = 3600000

        media_player = media_list_player.get_media_player()
        time_now = media_player.get_time()
        time_expected = time_now + number * time_factor

        print('go_forward() by MEASURE_TIME: number:', number, '   time_factor: ', time_factor)

        media_list_player.play()

        # Не знаю, надо ли сообщать о превышении размера трека
        # time_track = media_player.get_length()
        # if time_expected > time_track:
        #     media_player.set_time(time_track - 3000)
        #     say_text(word.END_OF_TRAC)
        # else:
        #     media_player.set_time(time_expected)
        media_player.set_time(time_expected)

    else:
        say_text(word.USER_NAME + word.MEASURE_UNDEFINED)


# Быстрая перемотка назад. Прыжок через несколько треков (например два трека)
# или через несколько секунд/минут/часов (например 20 секунд).
# Пока распознается только время или в секундах, или в минутах, или в часах.
# То есть время 2 минуты 6 секунд будет распознано как 8 секунд
def go_back(set_commands, result_text):
    number = get_number(set_commands, result_text)

    if not number:
        say_text(word.USER_NAME + word.NO_NUMBER)
        return

    if not set_commands.isdisjoint(word.SET_MEASURE_TRACK):
        if number > word.MAX_JUMP:
            say_text(word.LIMIT_MAX_JUMP)
            return

        if media_list_player.get_state() == vlc.State(0):
            play_vlc()

        for _ in range(number):
            media_list_player.previous()
            # todo
            # Возможно вынести время сна в voicehelper_friend_config.py, т.к.
            # на разных компах возможно надо другое время сна
            # time.sleep(0.5)
            time.sleep(0.01)
        # Не нашла ничего другого для перехода на заданное количество треков от ТЕКУЩЕГО трека.
        # А именно, не нашла как определить индекс текущего трека.
        # MediaList.index_of_item не подходит, т.к. ищет первое вхождение, а md в плейлисте может дублироваться
        print('go_back(): number:', number)

    elif not set_commands.isdisjoint(word.SET_MEASURE_TIME):
        time_factor = 1
        if not set_commands.isdisjoint(word.SET_MEASURE_SECOND):
            time_factor = 1000
        elif not set_commands.isdisjoint(word.SET_MEASURE_MINUTE):
            time_factor = 60000
        elif not set_commands.isdisjoint(word.SET_MEASURE_HOUR):
            time_factor = 3600000

        media_player = media_list_player.get_media_player()
        time_now = media_player.get_time()
        time_expected = time_now - number * time_factor

        print('go_forward() by MEASURE_TIME: number:', number, '   time_factor: ', time_factor)

        media_list_player.play()

        if time_expected < 1:
            media_player.set_time(1)
        else:
            media_player.set_time(time_expected)
    else:
        say_text(word.USER_NAME + word.MEASURE_UNDEFINED)


def execute_command(commands_to_execute, set_commands, result_text):
    if not commands_to_execute:
        say_text(word.USER_NAME + word.NO_COMMAND)
        print('execute_command():', word.NO_COMMAND)
        # save_current_status()
    elif not commands_to_execute.isdisjoint(word.SET_PLAY):
        # say_text(word.USER_NAME + word.PLAYER_START)
        # print('execute_command(): ', word.PLAYER_START)
        # Linux +
        # time.sleep(3)
        # Linux-
        play_vlc()
    elif not commands_to_execute.isdisjoint(word.SET_NEXT):
        say_text(word.USER_NAME + word.PLAYER_NEXT)
        print('execute_command(): ',  word.PLAYER_NEXT)
        play_next()
    elif not commands_to_execute.isdisjoint(word.SET_PREVIOUS):
        say_text(word.USER_NAME + word.PLAYER_PREVIOUS)
        print('execute_command(): ', word.PLAYER_PREVIOUS)
        play_previous()
    elif not commands_to_execute.isdisjoint(word.SET_GOTO):
        set_commands -= word.SET_GOTO
        print('execute_command(): GOTO / ', word.GOTO)
        go_to(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_FORWARD):
        set_commands -= word.SET_FORWARD
        say_text(word.USER_NAME + word.PLAYER_FORWARD)
        print('execute_command(): ', word.PLAYER_FORWARD)
        go_forward(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_BACK):
        commands_to_execute -= word.SET_BACK
        say_text(word.USER_NAME + word.PLAYER_BACK)
        print('execute_command(): ', word.PLAYER_BACK)
        go_back(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_PlAYLIST):
        set_commands -= word.SET_PlAYLIST
        # print('execute_command(): PlAYLIST /', word.PlAYLIST)
        set_playlist(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_SEARCH):
        commands_to_execute -= word.SET_SEARCH
        print('execute_command(): ', word.PLAYER_SEARCH)
        say_text(word.USER_NAME + word.PLAYER_SEARCH + ' '.join(commands_to_execute))
    elif not commands_to_execute.isdisjoint(word.SET_BYE):
        commands_to_execute -= word.SET_BYE
        print('execute_command(): ', word.BYE)
        say_text(word.USER_NAME + word.BYE)
        bye()
    else:
        say_text(word.USER_NAME + word.EXCEPT)
        print('execute_command(): ', word.EXCEPT)


def process_text_main(set_commands, result_text):
    set_commands -= {word.FRIEND}

    # Проверяем, есть ли в словах пользователя команды для выполнения
    commands_to_execute = set_commands & word.SET_ALL_COMMANDS

    # Если во множестве нет других слов (множество пустое), значит надо запросить команды
    if not commands_to_execute:
        say_text(word.USER_NAME + word.SAY_COMMAND)
        # Останавливаем поток, чтобы не попал шум (например речь друга) в речь пользователя
        stream.stop_stream()
        # и перезапускаем распознавание, чтобы убрать остатки былых слов
        rec.Reset()
        stream.start_stream()
        print('process_text_main():  ', word.USER_NAME, word.SAY_COMMAND)
        result_text = listen_to_user()
        result_text = result_by_words(result_text)
        set_commands = set(result_text)
        set_commands -= {word.FRIEND}
        # Проверяем, есть ли в словах пользователя команды для выполнения
        commands_to_execute = set_commands & word.SET_ALL_COMMANDS

    print('process_text_main(): result_text', result_text)
    print('process_text_main(): set_commands', set_commands)
    print('process_text_main(): commands_to_execute', commands_to_execute)
    execute_command(commands_to_execute, set_commands, result_text)


def bye():
    # f = open(word.FILE_STATUS, 'w')
    # f.write(current_playlist)
    # f.close()
    save_current_status()

    stream.stop_stream()
    stream.close()
    py_audio.terminate()
    print('main: Программа закрыта')


def main():
    global current_playlis
    record_seconds = 2

    say_text(word.PROGRAM_IS_RUNNING)

    try:
        listen = True
        while listen:
            for _ in range(0, RATE // CHUNK * record_seconds):
                data = stream.read(CHUNK)
                rec.AcceptWaveform(data)

            result_text = rec.PartialResult()

            print('\n')
            print('main() => result_text: ', result_text.replace("\n", ""), end='\n')

            if word.FRIEND in result_text:
                # В строке "друг" может быть в словах "вдруг", "другой" и проч.
                # Поэтому далее проверяем на точное соответствие слову друг
                result_text = result_by_words(result_text)
                set_commands = set(result_text)
                if word.FRIEND in set_commands:
                    # Как только услышали слово друг, плеер ставим на паузу, если он включен
                    if media_list_player.is_playing():
                        media_list_player.pause()

                    print('main(): The word friend has been discovered. set_commands=', set_commands, ', Running process_text_main')
                    process_text_main(set_commands, result_text)

            print('media_list_player.get_state() = ', media_list_player.get_state())
            media_player = media_list_player.get_media_player()
            n = media_player.get_position()
            print('main() =>  media_player.get_position() = ', n)

            med = media_player.get_media()
            # Получаем индекс текущего трека в плейлисте
            index_of_media = media_list.index_of_item(med)
            print('main() => index_of_media', index_of_media)


            # nn = media_player.audio_get_track()
            # print('media_player.audio_get_track()', nn)

            # print('audio_get_track_description = ', media_player.audio_get_track_description())

            # if not media_list_player.get_state() == vlc.State(0):
            #     med = media_player.get_media()
            #     # можно получить имя трека
            #     print('med.get_mrl() = ', med.get_mrl())
            #     # MediaList.index_of_item


            # vlc.State(6) (Ended) может быть или если список закончился или если файл не воспроизводится (не медиа формат)
            if media_list_player.get_state() == vlc.State(6):
                media_player = media_list_player.get_media_player()

                # Если воспроизведение еще не началось, то это не медиа файл
                if media_player.get_position() == 0:
                    media_list_player.next()
                elif media_player.get_position() == 1:
                    # плейлист закончился, начинаем его сначала
                    media_list_player.play_item_at_index(0)

                # Можно получить текущий воспроизводимый файл
                # med = media_player.get_media()
                # med.tracks_get() если None, то значит это не медиа файл.
                # Можно использовать это условие, чтобы перейти к следующему треку,
                # но это еще один объект. Пока он не нужен
                # b1=med.tracks_get()
                # Смотрела также эти варианты
                # b3=med.get_mrl() можно получить имя трека
                # b2=med.get_tracks_info()
                # b5=med.get_state()
                # b6=med.get_type()

            print('main(): media_list_player.get_state()', media_list_player.get_state())

            rec.Reset()
            stream.stop_stream()
            stream.start_stream()

    finally:
        stream.stop_stream()
        stream.close()
        py_audio.terminate()
        print('main: Программа закрыта')


if __name__ == '__main__':
    main()
