import os.path
import sys
from calendar import month
from pathlib import Path
from urllib.parse import unquote
import time
import  datetime
import json

# Для работы программа должна:
# 1. Слушать пользователя с микрофона и распознавать услышанное (переводить в текст)
#       1.1 Для того, чтобы слушать с микрофона используется pyaudio.
#       1.2 Для распознания услышанного используется KaldiRecognizer.
# 2. Говорить (произносить текст (переводить текст в голос))
#       2.1 Для перевода текста в голос используется менеджер синтеза речи speechd с движком rhvoice.

# Нужен микрофон. Для этого можно использовать pyaudio.
# Можно использовать SpeechRecognition, который все равно использует pyaudio.
# https://people.csail.mit.edu/hubert/pyaudio/docs/
# https://people.csail.mit.edu/hubert/pyaudio/
# PyAudio - это библиотека Python для работы со звуком в реальном времени - то есть для записи, воспроизведения и обработки аудиопотоков.
# PyAudio предоставляет Python связь с PortAudio v19 (кроссплатформенной библиотекой ввода-вывода аудио).
# По сути PyAudio оболочка PortAudio, упрощающая обработку звука в программах на Python.
# Основные функции, которые можно выполнять с помощью PyAudio:
# 1. Запись звука (вход для микрофона)
# 2. Воспроизведение звука (выход через динамик)
# 3. Обработка аудио в реальном времени
# 4. Приложения для потоковой передачи аудио
import pyaudio

# Для распознавания речи используем vosk - автономный API распознавания речи
from vosk import KaldiRecognizer
# Для ASUS
import numpy as np
from scipy.signal import resample_poly

def resample_audio(data, orig_rate=44100, target_rate=16000):
    # bytes → numpy int16
    audio = np.frombuffer(data, dtype=np.int16)

    # ресэмплинг
    resampled = resample_poly(audio, target_rate, orig_rate)

    # обратно в int16
    resampled = resampled.astype(np.int16)

    # numpy → bytes
    return resampled.tobytes()

# Были сообщения от ALSA типа "ALSA lib pcm_dmix.c:999:(snd_pcm_dmix_open) unable to open slave"
# и "jack server is not running or cannot be started"
# Помогло решение отсюда https://stackoverflow.com/questions/65079325/problem-with-alsa-in-speech-recognitionpython-3
# Хотя явно sounddevice нигде не используется, но import sounddevice помогает
import sounddevice

# Для преобразования текста в речь (для ответов друга) в Linux используем speechd (менеджер синтеза речи).
# speechd управляет синтезом речи в системе.
# Когда говорят несколько программ, speechd решает кто будет говорить первым, кого прервать, какую громкость приоритет дать.
# speechd принимает текст, передает нужному движку (в нашем случае rhvoice), управляет воспроизведением.
import speechd

# Для воспроизведения медиа файлов будем использовать vlc
import vlc

# Подключаем настройки и значения по умолчанию
import voicehelper_friend_config as word

# Настраиваем синтез речи через Speech Dispatcher (speechd) и говорим системе в качестве движка использовать rhvoice
# (то есть текст будет говориться голосом RHVoice)
client = speechd.SSIPClient('friends_voice')
client.set_output_module('rhvoice')
client.set_language('ru')
# set_rate скорость -100 очень медленно, 0 нормальная скорость, 100 очень быстро
# client.set_rate(15)
client.set_rate(5)
client.set_volume(3)
client.set_punctuation(speechd.PunctuationMode.SOME)


# RATE (частота дискретизации) - сколько сэмплов в секунду записывается.
# RATE = 16000 = 16000 "точек" звука в секунду
#     • 44100 = CD-качество
#     • 8000 = телефонное качество
# Критично важно
#     • Vosk обычно обучен на 16000 Hz
#     • если микрофон пишет в 48000 → происходит ресэмплинг
#     • плохой ресэмплинг = искажение речи
# Простыми словами: RATE → качество и совместимость с моделью (Vosk).
# Можно подстроить RATE под устройство. Если устройство реально работает в 48000, то лучше сделать так:
# RATE = int(dev['defaultSampleRate'])  # например 48000
# Делала проверку, оказалось что: requested = 16000Hz, got = 44100Hz. please, try the plug plugin
# Т.е я попросил 16000 Hz, а устройство реально работает на 44100 Hz и НЕ умеет напрямую писать в 16000.
# Почему это проблема: Vosk ожидает 16000 Hz.
# Если подать 44100 как 16000, речь «ускоряется», искажается распознавание, ломается
# Поэтому лучший вариант (лучший баланс), оставить: RATE = 16000
# Вариант 2 (правильный, но сложнее), записывать в 44100, потом ресэмплить самому
# RATE = 44100
# и потом конвертировать в 16000 перед подачей в Vosk
# Но! Это: сложнее, нагружает CPU, не всегда лучше
# Важно: Vosk официально лучше всего работает на 16000, но на практике 44100 иногда тоже ок
#
# CHUNK (размер блока) - сколько сэмплов читается за один раз.
# Время одного CHUNK = CHUNK / RATE
# Если CHUNK = 8000, то 8000 / 16000 = 0.5 секунды, то есть ты читаешь звук кусками по полсекунды
# Большой CHUNK (как у тебя): высокая задержка, грубая нарезка речи, хуже реакция, хуже распознавание коротких слов
# Маленький CHUNK (1024–2048): плавный поток, лучше для Vosk, меньше потерь.
# На слабом ноутбуке:
# Большой CHUNK = меньше вызовов → вроде легче CPU
# НО, если поток "рвется" → хуже результат
# Вывод: оптимально: CHUNK = 1024 или 2048
# Простыми словами: CHUNK → насколько "гладкий" поток
#
# frames_per_buffer это размер буфера на уровне аудиосистемы:
# stream = py_audio.open(..., frames_per_buffer=CHUNK)
# Обычно = CHUNK (как у тебя)
# Что делает: определяет, сколько данных накапливается перед отдачей, влияет на задержку и стабильность:
# Маленький буфер: низкая задержка, риск underrun (пропуски)
# Большой буфер: стабильнее, но задержка выше
# На слабом ноутбуке: лучше чуть больше буфер, чем слишком маленький
# Простыми словами: frames_per_buffer → стабильность vs задержка
#
# Связка параметров (самое важное). Вот где многие ошибаются: for _ in range(0, RATE // CHUNK * record_seconds):
# Подставим твои значения:
# RATE = 16000
# CHUNK = 8000
# record_seconds = 2 (обработка «кусками по 2 секунды»)
# RATE // CHUNK * record_seconds = 4, → всего 4 итерации. Ты читаешь всего 4 куска аудио
# Почему это плохо: речь режется кусками, Vosk не получает непрерывный поток, ухудшается контекст.
#
#
# rec.Reset() - это метод из Vosk.
# Он: полностью сбрасывает внутреннее состояние распознавателя, удаляет: накопленный аудиоконтекст, текущую гипотезу фразы.
# По сути: «забудь всё, что ты только что слышал».
# Почему это плохо: распознавание речи — это контекстная штука:
# "привет как дела" лучше распознаётся вместе, чем по кускам: "привет" → reset → "как" → reset → "дела"
# После Reset(): модель начинает «с нуля», возрастает вероятность ошибок
#
# stream.stop_stream() - из PyAudio
# Он: останавливает захват аудио с микрофона, поток больше не читает данные.
#
# stream.start_stream() снова запускает поток записи
#
# Чем плохо rec.Reset(), stream.stop_stream(), stream.start_stream()
# Ты: рвешь аудиопоток, сбрасываешь контекст. Для распознавания речи это очень плохо.
# Как делают обычно: читают поток непрерывно, передают маленькие куски, не делают Reset постоянно.
# rec.Reset(), stream.stop_stream(), stream.start_stream() означает:
# выкинули весь контекст распознавания, остановили поток, снова запустили (с разрывом).
# На практике это даёт: 1. потерю кусочков речи, между stop/start часть звука просто теряется,
# 2. разрывы в аудио, поток становится: [кусок] — пауза — [кусок] — пауза
# 3. ухудшение распознавания особенно на слабом ноутбуке при шуме, при быстрой речи.
# 4. «Бредовые» слова потому что модель не видит контекста и пытается угадать по обрывкам
# Когда это вообще нужно? Редко, но бывает,  если ты хочешь:
# жёстко разделять команды, обрабатывать строго фиксированные куски (например 2 секунды).
# Но для живой речи — это плохая идея.
# То есть rec.Reset(), stream.stop_stream(), stream.start_stream() делает:
# сброс контекста, разрыв аудио, потерю данных и прямо ухудшает распознавание, особенно на слабом железе.
#
# Как правильно: поток никогда не останавливают, Reset() почти не используют, доверяют rec.AcceptWaveform(data).
# rec.AcceptWaveform(data) сам понимает, когда фраза закончена, возвращает финальный результат.
#
# Рекомендуемые настройки для слабого ноутбука:
# RATE = 16000
# CHUNK = 1024  # или 2048
# frames_per_buffer = CHUNK
#
# Model('/home/.../vosk_model_small_ru/') - маленькая модель: быстрее, но менее точная.
# На слабом ноуте это усугубляется: хуже звук + слабый CPU = сильная деградация
# Можно попробовать большую модель (если потянет) или наоборот оптимизировать поток.
# Vosk ждёт 16000 Hz
# Есть 2 варианта:
# Вариант 1 (проще и чаще норм):
# Если устройство нормально принимает 16000 (у тебя, похоже, да), то лучший вариант оставить:
# RATE = 16000
# Вариант 2 (если есть проблемы)
# Если окажется, что устройство реально пишет в 48000 и 16000 даёт плохой звук, тогда:
# записывать в 48000, делать ресэмплинг в Python (но это сложнее и тяжелее для CPU).

# Чтобы использовать PyAudio, сначала создаем экземпляр PyAudio, который получит
# системные ресурсы для PortAudio (короче подключаемся к микрофону)
py_audio = pyaudio.PyAudio()

ASUS = False
# Поиск usb микрофона
def find_input_device(p, name_part):
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if name_part in dev['name'] and dev['maxInputChannels'] > 0:
            return i
    return None
DEVICE_INDEX = find_input_device(py_audio, "USB Audio")
if DEVICE_INDEX != None:
    ASUS = True

# Какое устройство берётся по умолчанию?
# Если в PyAudio ты пишешь: stream = p.open(input=True, ...), без input_device_index,
# то используется: default input device (системное устройство по умолчанию)
# В выводе PyAudio:
# 4 pulse 32
# 5 default 32
#
#  pulse — через PulseAudio / PipeWire
# default — системный дефолт
#print("Используем устройство:", DEVICE_INDEX)
# for i in range(py_audio.get_device_count()):
#     print(i, py_audio.get_device_info_by_index(i)['name'])


CHANNELS = 1  # моно
# RATE = 44100  # частота дискретизации - кол-во фреймов в секунду
if ASUS:
    RATE = 44100
else:
    RATE = 16000
# CHUNK кол-во фреймов за один "запрос" к микрофону - тк читаем по кусочкам
if ASUS:
    CHUNK = 4096
else:
    CHUNK = 1024
FORMAT = pyaudio.paInt16  # глубина звука = 16 бит = 2 байта

model = word.MODEL_VOSK

# Создаём аудиопоток (stream), через который потом читаем звук с микрофона или пишем его.
# py_audio.open: открывает аудиоустройство (микрофон), настраивает параметры (частота, формат, каналы),
# создаёт объект stream, резервирует устройство (оно становится «занято»).
# (input=True означает, что мы читаем звук (микрофон), если было бы output=True, то это уже вывод звука (динамики)
# про остальные параметры см. выше)
# Потом через stream читаем звук.
# Т.е. p.open() → создаёт канал, stream.read() → читает звук.
# p.open(...) только создаёт поток, stream.start_stream() - реально начинает запись
if DEVICE_INDEX == None:
    stream = py_audio.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK,
                           # input_device_index=DEVICE_INDEX
                           )
else:
    stream = py_audio.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK,
                           input_device_index=DEVICE_INDEX,
                           )

stream.start_stream()


# Большинство команд к другу касаются плеера, поэтому он должен быть всегда доступен
vlc_instance = vlc.Instance()
media_list_player = vlc_instance.media_list_player_new()
media_list = vlc_instance.media_list_new()

len_playlist = 0

user_name = word.USER_NAME

def say_text(text):
    # text_len = len(text)
    # time_len = text_len / 10 - 7

    client.speak(text)
    # time.sleep(2)
    #
    # if time_len > 0:
    #     time.sleep(time_len)


def play_vlc(playlist_for_play='SomethingWrong.m3u'):
    global len_playlist
    global media_list
    global media_list_player

    #print('play_vlc() => ', media_list_player.get_state())

    # Если плеер уже запущен, но находится в состоянии пауза, то запускаем его (продолжаем играть)
    if media_list_player.get_state() == vlc.State(4) :
        #print('play_vlc() => elif - State(4) - Paused')

        # Пауза - это когда сказали друг и больше нет никакой команды => воспроизведение просто ставится на паузу =>
        # (см. # Как только услышали слово друг, плеер ставим на паузу, если он включен)
        # все остается по-прежнему, просто возобновляем работу плеера
        statuses = read_statuses_from_track()
        # say_text(word.USER_NAME + word.START_ON_PLAYLIST + statuses["current_playlist_name"])
        say_text(user_name + word.START_ON_PLAYLIST + statuses["current_playlist_name"])
        time.sleep(2)
        media_list_player.pause()

    #  Stopped происходит только когда сказали список и название списка
    elif media_list_player.get_state() == vlc.State(5) :
        # say_text(word.USER_NAME + word.START_ON_PLAYLIST + playlist_for_play)
        say_text(user_name + word.START_ON_PLAYLIST + playlist_for_play)
        #print('play_vlc() => elif - State(5) Stopped')

        # Получаем название каталога с плейлистами
        dir_playlst = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST
        # Формируем полный путь к плейлисту
        new_playlist_path = dir_playlst + '/' + playlist_for_play + '.m3u'
        #print('play_vlc() => new_playlist_path = ', new_playlist_path)

        playlist_list = load_playlist(new_playlist_path)

        len_playlist = len(playlist_list)

        if len_playlist == 0:
            say_text(word.PLAYLIST_EMPTY)
            return

        media_list = vlc_instance.media_list_new()

        for song in playlist_list:
            media_list.add_media(song.rstrip())

        media_list_player.set_media_list(media_list)

        # Получаем из файла данные о текущем треке и текущей позиции.
        # Выбираем трек и позицию в нем для воспроизведения

        name_file_status = word.FILE_STATUS
        current_track_index = 0
        current_track_position = 0

        # Считываем данные из файла CurrentStatus.json (to do перенести в обработчик?)
        try:
            with (open(name_file_status, 'r', encoding='utf-8') as file):
                loaded_data = json.load(file)
                #print('play_vlc() =>  json файл считан')
                #print('play_vlc() => playlist_for_play = ', playlist_for_play)

                #print('play_vlc() => new_playlist_path = ', new_playlist_path)

                seek_playlist = loaded_data[playlist_for_play]
                current_track_index = seek_playlist['current_track_index']
                current_track_position = seek_playlist["current_track_position"]

                #print('play_vlc() => current_track_index = ', current_track_index)
                #print('play_vlc() => current_track_position = ', current_track_position)

                #print('play_vlc() считанные данные о запускаемом плейлисте')
                #print('read_statuses_from_file() =>  current_track_index = ', current_track_index,
                      #'  current_track_position = ', current_track_position)
                current_playlist = playlist_for_play
        except FileNotFoundError:
            #print("FileNotFoundError")
            current_playlist = word.PlAYLIST_BY_DEFAULT
            # print('Чтение json. Файл не найден или поврежден. Берем значения по умолчанию')
        except json.JSONDecodeError:
            #print('JSONDecodeError')
            current_playlist = word.PlAYLIST_BY_DEFAULT
        except Exception as e:
            # Другие возможные ошибки при работе с файлом
            print(f"Произошла другая ошибка: {e}")

        media_list_player.play_item_at_index(current_track_index)
        #print('play_vlc() => current_track_index = ', current_track_index)

        media_player = media_list_player.get_media_player()
        media_player.set_position(current_track_position)
        #print('play_vlc() => current_track_position = ', current_track_position)

        #print('play_vlc() => State(5) ')
        media_list_player.play()
    else:
        # Все остальные статусы, в том числе
        # State.NothingSpecial = State(0) - когда программа только запущена, но плеер еще не запускали
        # State.Ended = State(6) - когда плейлист закончился
        # State.Error = State(7)
        # State.Opening = State(1) - при открытии файла
        # State.Playing = State(3)
        # to do Переделать только на статус Opening?
        #
        # Создаем новый плейлист и загружаем в него список
        # Плейлист из файла загружаем в список (список, а не кортеж, т.к. планируется добавление в плейлист?)
        # Плейлисты будут храниться в ~/VoiceFriend_PlayLists/
        #print('play_vlc() => else - State(1, 6 etc) - Ended, Opening etc ')
        statuses = read_statuses_from_file()

        # При любой проблеме с чтением файла CurrentStatus в read_statuses_from_file
        # current_playlist присваивается значение word.PlAYLIST_BY_DEFAULT
        # В таком случае предлагаем выбрать новй плейлист
        # То есть используем current_playlist==word.PlAYLIST_BY_DEFAULT как признак для того чтобы предложить выбрать плейлист
        if statuses["current_playlist"]==word.PlAYLIST_BY_DEFAULT:
            choose_playlst()
            return

        current_playlist_name = Path(statuses["current_playlist"]).stem
        #print('play_vlc() => current_playlist_name = ', current_playlist_name)
        say_text(user_name + word.START_ON_PLAYLIST + current_playlist_name)
        time.sleep(2)

        playlist_list = load_playlist(statuses["current_playlist"])

        len_playlist = len(playlist_list)

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
        #print('play_vlc() => current_track_index = ', statuses["current_track_index"])

        media_player = media_list_player.get_media_player()
        media_player.set_position(statuses["current_track_position"])
        #print('play_vlc() => current_track_position = ', statuses["current_track_position"])

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

#region 'Статусы плейлистов и записей (какой текущий, позиция): чтение, сохранение'
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
            #print('read_statuses_from_file() => json файл считан')
            # Получаем последний плейлист
            current_playlist = loaded_data.get("current_playlist", word.PlAYLIST_BY_DEFAULT)
            #print('read_statuses_from_file() => current_playlist = ', current_playlist)
            # Получаем последний трек
            if current_playlist == word.PlAYLIST_BY_DEFAULT:
                current_track_index = 0
                current_track_position = 0
            else:
                dir_name_track = Path(current_playlist)
                #print('read_statuses_from_file() => dir_name_track = ', dir_name_track)
                dir_track = dir_name_track.parent
                #print('read_statuses_from_file() => dir_track = ', dir_track)
                current_playlist_name = dir_name_track.stem
                #print('read_statuses_from_file() => current_playlist_name = ', current_playlist_name)
                seek_playlist = loaded_data[current_playlist_name]
                current_track_index = seek_playlist['current_track_index']
                current_track_position = seek_playlist["current_track_position"]
            #print('read_statuses_from_file() =>  current_track_index = ',current_track_index, '  current_track_position = ', current_track_position)
    except FileNotFoundError:
        #print("FileNotFoundError")
        # Здесь и ниже current_playlist = word.PlAYLIST_BY_DEFAULT используется в play_vlc, когда не удалось прочитать
        # статусы из CurrentStatus to do?
        current_playlist = word.PlAYLIST_BY_DEFAULT
        current_track_index = 0
        current_track_position = 0
    except json.JSONDecodeError:
        #print('JSONDecodeError')
        current_playlist = word.PlAYLIST_BY_DEFAULT
        current_track_index = 0
        current_track_position = 0
        # Возможно если json поломан, то лучше удалить CurrentStatus to do
    except Exception as e:
        # Другие возможные ошибки при работе с файлом
        #print(f"Произошла другая ошибка: {e}")
        #print('JSONDecodeError')
        # Не уверена, что так правильно to do?
        current_playlist = word.PlAYLIST_BY_DEFAULT
        current_track_index = 0
        current_track_position = 0
        # Возможно если ничего не получается, надо удалить CurrentStatus? to do

    statuses = {"current_playlist": current_playlist, "current_track_index": current_track_index,
                "current_track_position": current_track_position}

    return statuses


def read_statuses_from_track():
    global media_list_player
    global media_list

    dir_playlist = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST

    media_player = media_list_player.get_media_player()
    # Получаем позицию в текущем треке
    position_in_media = media_player.get_position()
    #print('read_statuses_from_track() => media_player.get_position() = ', position_in_media)

    med = media_player.get_media()
    #print('read_statuses_from_track() =>media_list_player.get_state() = ', media_list_player.get_state())
    # Получаем индекс текущего трека в плейлисте
    index_of_media = media_list.index_of_item(med)
    if index_of_media == -1:
        # При первом старте, когда еще не был запущен ни один трек, сохранять нечего, поэтому statuses пустой
        statuses = {}
        return statuses


    #print('read_statuses_from_track() => index_of_media', index_of_media)

    # Получаем имя текущего плейлиста
    mrl = med.get_mrl()
    decoded_mrl = unquote(mrl)
    dir_name_track = Path(decoded_mrl)
    dir_track = dir_name_track.parent
    current_playlist_name = dir_track.name
    # to do Если PlAYLIST_BY_DEFAULT, то сохранять в каталог с программой
    # Здесь возможно надо исправить и вообще подумать нужен ли плейлист по умолчанию to do?
    if current_playlist_name == word.PlAYLIST_BY_DEFAULT:
        current_playlist = current_playlist_name + '.m3u'
    else:
        current_playlist = dir_playlist + '/' + current_playlist_name + '.m3u'

    statuses = {"current_playlist_name": current_playlist_name, "current_playlist": current_playlist,
                "current_track_index": index_of_media, "current_track_position": position_in_media}

    return statuses


def save_current_status():
    name_file_status = word.FILE_STATUS
    dir_playlist = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST

    # Получаем данные закрываемого плейлиста (который сейчас сменим на новый плейлист)
    statuses = read_statuses_from_track()

    if not statuses:
        #print("save_current_status - not statuses")
        # При первом старте, когда еще не был запущен ни один трек, сохранять нечего, поэтому statuses пустой
        return

    # Считываем данные из json файла в loaded_data, добавляем в loaded_data данные закрываемого плейлиста
    # и записываем loaded_data опять в json файл
    try:
        with open(name_file_status, 'r', encoding='utf-8') as file:
            loaded_data = json.load(file)
            #print("save_current_status - loaded_data: " , loaded_data)
    except (json.JSONDecodeError, FileNotFoundError):
        #print('json файла поврежден. Создаем новый пустой json файл')
        loaded_data = {}
    except Exception as e:
        # Другие возможные ошибки при работе с файлом
        #print(f"Произошла другая ошибка: {e}")
        loaded_data = {}

    #print('save_current_status() => loaded_data из файла: ', loaded_data)

    current_playlist = statuses["current_playlist"]
    #print("current_playlist: ", current_playlist)
    loaded_data["current_playlist"] = current_playlist

    current_playlist_name = statuses["current_playlist_name"]
    current_track_position = statuses["current_track_position"]
    #print("current_playlist_name: ", current_playlist_name)
    #print("current_track_position: ", current_track_position)

    current_track_index = statuses["current_track_index"]
    #print("current_track_index: ", current_track_index)
    if current_track_index < 0:
        current_track_index = 0
        current_track_position = 0

    track_info = {"current_track_index": current_track_index,
                  "current_track_position": current_track_position}
    loaded_data[current_playlist_name] = track_info

    #print('save_current_status() => loaded_data в файл: ', loaded_data)

    with open(name_file_status, 'w', encoding='utf-8') as file:
        json.dump(loaded_data, file, ensure_ascii=False, indent=4)
#endregion


#region 'Плейлисты: обработка команды список, загрузка плейлиста, выбор плейлиста'

# Обрабатывает команду список
def set_playlist(set_commands, result_text):
    global media_list_player
    global media_list

    # Получаем название каталога с плейлистами из домашней папки
    dir_playlst = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST
    # Проверяем есть ли такой каталог
    if not os.path.isdir(dir_playlst):
        #print('Нет каталога с плейлистами. Сообщаем пользователю.')
        say_text(word.DIR_PLAYLIST_NO)
        # Может быть сюда вставить загрузку плейлиста по умолчанию? to do
        return

    # Если каталог есть, то получаем в список все названия файлов из этого каталога
    list_of_file = os.listdir(dir_playlst)
    #print('set_playlist() => Каталог с плейлистами есть.Список файлов')
    #print(list_of_file)

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
        say_text(user_name + word.ALL_PLAYLIST_1)
        time.sleep(2)
        for name in set_of_playlist:
            say_text(os.path.splitext(os.path.basename(name))[0])
            time.sleep(0.05)
            # Это чтобы паузы были между названиями

        # И предлагаем выбрать один из них
        say_text(user_name + word.ALL_PLAYLIST_2)
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
            # В Windows плейлисты делала в vlc. По умолчанию плейлист сохраняет путь к файлу в url формате,
            # но в Linux при сохранении плейлиста в vlc url путь с русскими буквами перекодируется в английский.
            # Поэтому для создания плейлиста в Linux использую JuK/CreatePlaylists.py, а он создает плейлисты с обычными путями.
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


def choose_playlst():
    # Повтор кода из set_playlist. to do ?
    dir_playlst = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST
    # Проверяем есть ли такой каталог
    if not os.path.isdir(dir_playlst):
        #print('Нет каталога с плейлистами. Сообщаем пользователю.')
        say_text(word.DIR_PLAYLIST_NO)
        # Может быть сюда вставить загрузку плейлиста по умолчанию? to do
        # return

    # Если каталог есть, то получаем в список все названия файлов из этого каталога
    list_of_file = os.listdir(dir_playlst)
    #print('set_playlist() => Каталог с плейлистами есть.Список файлов')
    #print(list_of_file)

    set_of_playlist = set()
    for file in list_of_file:
        if file.endswith('.m3u'):
            name_playlist = file[:-4]
            set_of_playlist.add(name_playlist)

    say_text(user_name + word.ALL_PLAYLIST_3)
    time.sleep(2)
    for name in set_of_playlist:
        say_text(os.path.splitext(os.path.basename(name))[0])
        time.sleep(0.05)
        # Это чтобы паузы были между названиями

    # И предлагаем выбрать один из них
    say_text(user_name + word.ALL_PLAYLIST_2)
#endregion


#region 'Переходы впред, назад, к'
def play_next():
    global media_list_player
    global media_list

    media_list_player.next()


def play_previous():
    global media_list_player
    global media_list

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
    #print('set_commands = ', set_commands)
    #print('result_text = ', result_text)
    set_number_in_result = set_commands & word.All_NAME_NUMBER
    #print('set_number_in_result = ', set_number_in_result)

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

    #for w in result_text:
    for w in set_commands:
        if w in set_number_in_result:
            number_in_result.append(w)

    

    #print('number_in_result = ', number_in_result)

    for w in word.NAME_THOUSAND:
        if w in number_in_result:
            number_thousand = 1

            index_thousand = number_in_result.index(w)
            thousand = number_in_result[:index_thousand + 1]

            for ww in thousand:
                number_thousand = number_thousand * word.NAME_NUMBER_DICT[ww]

            is_thousand = True
            break
    #print('number_thousand = ', number_thousand)

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
    #print('number_hundred = ', number_hundred)
    number_residue = number_in_result[:]

    #print('number_residue = ', number_residue)

    if is_thousand:
        number_residue = number_in_result[index_thousand+1:]
    #print('number_residue = ', number_residue)
    
    if is_hundred:
        number_residue = number_in_result[index_hundred+1:]
    #print('number_residue = ', number_residue)
    
    for ww in number_residue:
        number = number + word.NAME_NUMBER_DICT[ww]
    #print('number_residue = ', number_residue)
    
    number = number_thousand + number_hundred + number
    #print('number = ', number)

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
    global media_list_player
    global media_list

    number = get_number(set_commands, result_text)
    #print('go_to(): number: ', number)

    if not number:
        say_text(user_name + word.NO_NUMBER)
        return

    if not set_commands.isdisjoint(word.SET_MEASURE_TRACK):
        if media_list_player.get_state() == vlc.State(0):
            play_vlc()
            media_list_player.set_pause(1)

        if number > len_playlist - 2:
            say_text(user_name + word.number_greater_len_pl(number, len_playlist-2))
            return

        say_text(user_name + word.GOTO_TRACK + str(number))

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
        say_text(user_name + word.MEASURE_UNDEFINED)


# Быстрая перемотка вперед. Прыжок через несколько треков (например два трека)
# или через несколько секунд/минут/часов (например 20 секунд)
# Пока распознается только время или в секундах, или в минутах, или в часах.
# То есть время 2 минуты 6 секунд будет распознано как 8 секунд
def go_forward(set_commands, result_text):
    global media_list_player
    global media_list

    number = get_number(set_commands, result_text)

    #print('number = ', number)

    if not number:
        say_text(user_name + word.NO_NUMBER)
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
        #print('go_forward() by MEASURE_TRACK: number:', number)

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

        #print('go_forward() by MEASURE_TIME: number:', number, '   time_factor: ', time_factor)

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
        say_text(user_name + word.MEASURE_UNDEFINED)


# Быстрая перемотка назад. Прыжок через несколько треков (например два трека)
# или через несколько секунд/минут/часов (например 20 секунд).
# Пока распознается только время или в секундах, или в минутах, или в часах.
# То есть время 2 минуты 6 секунд будет распознано как 8 секунд
def go_back(set_commands, result_text):
    global media_list_player
    global media_list

    number = get_number(set_commands, result_text)

    if not number:
        say_text(user_name + word.NO_NUMBER)
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
        #print('go_back(): number:', number)

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

        #print('go_forward() by MEASURE_TIME: number:', number, '   time_factor: ', time_factor)

        media_list_player.play()

        if time_expected < 1:
            media_player.set_time(1)
        else:
            media_player.set_time(time_expected)
    else:
        say_text(user_name + word.MEASURE_UNDEFINED)
#endregion


#region 'Дата, время'
def get_value(key, name_list, name_dict):
    part_day = ''

    for item in name_list:
        if key in item:
            ind = name_list.index(item)
            part_day = name_dict.get(ind,'')
            break

    return part_day


def say_time():
    hour = datetime.datetime.now().hour
    hour_pm = hour if hour < 13 else hour - 12
    minute = datetime.datetime.now().minute

    minute_text = word.MINUTE_BY_WORD.get(minute, '') + ' ' + get_value(minute, word.LIST_MINUTE, word.NAME_MINUTE)

    # Время в формате pm
    # hour_pm_text = (word.FOR_TIME_NOW + get_value(hour, word.LIST_PART_DAY, word.NAME_PART_DAY)  + '. ' +
    #         word.HOUR_BY_WORD.get(hour_pm, '') + ' ' + get_value(hour_pm, word.LIST_HOUR, word.NAME_HOUR) + ' ')
    hour_pm_text = word.HOUR_BY_WORD.get(hour_pm, '') + ' ' + get_value(hour_pm, word.LIST_HOUR, word.NAME_HOUR) + ' ' + \
                       get_value(hour, word.LIST_PART_DAY, word.NAME_PART_DAY) + ' '

    say_text(hour_pm_text + minute_text)


def say_day():
    datetime_now = datetime.datetime.now()
    weekday_now = datetime_now.isoweekday()
    day_now = datetime_now.day
    month_now = datetime_now.month

    weekday_now_text = word.TODAY + ' ' + word.DAY_OF_WEEK.get(weekday_now, '')
    day_now_text = word.DAY_OF_MONTH.get(day_now, '') + ' ' +word.MONTH_NAME.get(month_now)

    say_text(weekday_now_text)
    say_text(day_now_text)
    # say_text(weekday_now_text + ' ' + day_now_text)
#endregion

def execute_command(commands_to_execute, set_commands, result_text):
    if not commands_to_execute:
        #say_text(user_name + word.NO_COMMAND)
        #print('execute_command():', word.NO_COMMAND)
        save_current_status()
    elif not commands_to_execute.isdisjoint(word.SET_PLAY):
        #print('execute_command(): ', word.PLAYER_START)
        play_vlc()
    elif not commands_to_execute.isdisjoint(word.SET_NEXT):
        say_text(user_name + word.PLAYER_NEXT)
        #print('execute_command(): ',  word.PLAYER_NEXT)
        play_next()
    elif not commands_to_execute.isdisjoint(word.SET_PREVIOUS):
        say_text(user_name + word.PLAYER_PREVIOUS)
        #print('execute_command(): ', word.PLAYER_PREVIOUS)
        play_previous()
    #elif not commands_to_execute.isdisjoint(word.SET_GOTO):
    #    set_commands -= word.SET_GOTO
    #    print('execute_command(): GOTO / ', word.GOTO)
    #    go_to(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_FORWARD):
        set_commands -= word.SET_FORWARD
        say_text(user_name + word.PLAYER_FORWARD)
        #print('execute_command(): ', word.PLAYER_FORWARD)
        go_forward(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_BACK):
        commands_to_execute -= word.SET_BACK
        say_text(user_name + word.PLAYER_BACK)
        #print('execute_command(): ', word.PLAYER_BACK)
        go_back(set_commands, result_text)
    elif not commands_to_execute.isdisjoint(word.SET_PlAYLIST):
        set_commands -= word.SET_PlAYLIST
        #print('execute_command(): PlAYLIST /', word.PlAYLIST)
        set_playlist(set_commands, result_text)
    #elif not commands_to_execute.isdisjoint(word.SET_SEARCH):
    #    commands_to_execute -= word.SET_SEARCH
    #    print('execute_command(): ', word.PLAYER_SEARCH)
    #    say_text(user_name + word.PLAYER_SEARCH + ' '.join(commands_to_execute))
    elif not commands_to_execute.isdisjoint(word.SET_TIME):
        commands_to_execute -= word.SET_TIME
        #print('execute_command(): ', word.SET_TIME)
        say_time()

    elif not commands_to_execute.isdisjoint(word.SET_DAY):
        commands_to_execute -= word.SET_DAY
        #print('execute_command(): ', word.SET_TIME)
        say_day()

    #elif not commands_to_execute.isdisjoint(word.SET_I_CAN_DO):
    #    commands_to_execute -= word.SET_I_CAN_DO
        # Рассказ о том что умеет друг в json разбитый по областям (общее, трек, плейлист)
        # поэтому можно организовать прослушивание конкретной области. Поэтому commands_to_execute -= word.SET_I_CAN_DO
        # i_can_do()

    elif not commands_to_execute.isdisjoint(word.SET_BYE):
        commands_to_execute -= word.SET_BYE
        #print('execute_command(): ', word.BYE)
        say_text(user_name + ', ' + word.BYE)
        bye()
    else:
        #say_text(user_name + word.EXCEPT)
        print('execute_command(): ', word.EXCEPT)


def bye():
    save_current_status()

    stream.stop_stream()
    stream.close()
    py_audio.terminate()
    #print('main: Программа закрыта')

#print('Режим ASUS = ', ASUS)

MODE_WAKE = 0
MODE_COMMAND = 1
MODE_MOVE = 2

def main():
    global stream
    global current_playlis
    global media_list_player
    global media_list

    time_to_bye = datetime.datetime.now().replace(hour=word.TIME_TO_BYE_HOUR, minute=word.TIME_TO_BYE_MINUTE)

    #print('')
    wake_grammar = json.dumps(["эй подруга",
        "пой", "играй", "плейлист", "список", "следующий", "следующая",
        "предыдущий","предыдущая", "время", "сегодня", "день",
        # плейлисты
        "песни", "музыка", "барды", "библия", "духовное", "здоровье", "зрение",
        "утро", "вечер", "память","молитвы", 
        # движение
        "вперёд", "назад", "минуту", "минуты", "минут", "секунду", "секунды",
        "секунд", "час", "часа", "часов","трек", "трека", "треков",
        "одну", "две", "три", "четыре","пять", "шесть", "семь",
        "восемь", "девять", "десять", "одиннадцать", "двенадцать", "тринадцать",
        # добавила. Убрать если затормозит распознование +
        "один", "два", 
        # -
        "четырнадцать", "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать",
        "девятнадцать","двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят",
        "семьдесят", "восемьдесят", "девяносто","сто", "двести"
    ], ensure_ascii=False)

    wake_rec = KaldiRecognizer(model, 16000, wake_grammar)

    mode = MODE_WAKE
    active_rec = wake_rec

    # буфер текста
    partial_text = ""
    final_text = ""

    # Счетчики wake word
    wake_counter = 0
    WAKE_THRESHOLD = 5

    # таймеры
    last_speech_time = time.time()
    silence_timeout = 1.1   # пауза = конец фразы
    command_timeout = 5.0
    #print(" command_timeout = ", command_timeout) 

    command_start_time = 0

    #print("Ожидание ключевого слова...")

    try:
        while True:
            # Надо выключить в назначенное время
            if datetime.datetime.now() > time_to_bye:
                #print('Пора спать!')
                # Ставим плеер на паузу, если он включен
                if media_list_player.is_playing():
                    media_list_player.pause()

                #say_text(user_name + ', ' + word.SAY_TO_BYE_1)
                #say_time()
                #say_text(word.SAY_TO_BYE_2)

                #print('bye')
                bye()

            
            data = stream.read(CHUNK, exception_on_overflow=False)
            if ASUS:
                data16 = resample_audio(data, 44100, 16000)
            else:
                data16 = data

            # ===== распознавание =====
            if wake_rec.AcceptWaveform(data16):
                result = json.loads(active_rec.Result())
                text = result.get("text", "")

                if text:
                    final_text += " " + text
                    last_speech_time = time.time()
                    #print('final_text active_rec :', final_text)

            else:
                partial = json.loads(active_rec.PartialResult()).get("partial", "")
                if partial:
                    partial_text = partial
                    last_speech_time = time.time()

                    # СЧЁТЧИК WAKE WORD
                    if "эй подруга" in partial_text:
                        wake_counter += 1
                        #print("wake_counter:", wake_counter)
                    else:
                         wake_counter = 0
                         #print("wake_counter:", wake_counter)

            # текущий текст
            current_text = (final_text + " " + partial_text).strip()

            # ===== окончание фразы по паузе =====
            if current_text and (time.time() - last_speech_time > silence_timeout):
                #print("current_text окончание фразы по паузе :", current_text)

                #print("wake_counter", wake_counter)
                if wake_counter >= WAKE_THRESHOLD:
                    
                    if "эй подруга" in current_text:
                        
                        wake_counter = 0
                        if media_list_player.is_playing():
                            media_list_player.pause()
                            save_current_status()
                        #print("Wake word: Услышали слово друг current_text:)", current_text)

                        words = set(current_text.split())
                        #print('words: ', words)

                        set_commands = words - {"эй", "подруга"}

                        #print("set_commands: ", set_commands)

                        if set_commands:
                            execute_command(words, words, current_text.split())
                            #print("if set_commands:")

                            wake_rec.Reset()
                            partial_text = ""
                            final_text = ""
                            wake_counter = 0

                # ===== очистка буфера =====
                partial_text = ""
                final_text = ""

        media_player = media_list_player.get_media_player()

        # vlc.State(6) (Ended) может быть или если список закончился или если файл не воспроизводится (не медиа формат)
        if media_list_player.get_state() == vlc.State(6):
            media_player = media_list_player.get_media_player()

            # Если воспроизведение еще не началось, то это не медиа файл
            if media_player.get_position() == 0:
                media_list_player.next()
            elif media_player.get_position() == 1:
                # плейлист закончился, начинаем его сначала
                media_list_player.play_item_at_index(0)

    finally:
        stream.stop_stream()
        stream.close()
        py_audio.terminate()


if __name__ == '__main__':
    main()
