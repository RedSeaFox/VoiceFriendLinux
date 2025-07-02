import os.path
import time
# Нужен микрофон. Для этого можно использовать pyaudio.
# Можно использовать SpeechRecognition, который все равно использует pyaudio.
# PyAudio предоставляет Python связь с PortAudio v19 (кроссплатформенной библиотекой ввода-вывода аудио)
# https://people.csail.mit.edu/hubert/pyaudio/docs/
# https://people.csail.mit.edu/hubert/pyaudio/
import pyaudio
# Для распознавания речи используем vosk - автономный API распознавания речи
from vosk import KaldiRecognizer
# Для преобразования текста в речь (для ответов друга) используем pyttsx3
import pyttsx3
# Для воспроизведения аудио файлов будем использовать vlc
import vlc

import voicehelper_friend_config as word


CHANNELS = 1  # моно
RATE = 16000  # частота дискретизации - кол-во фреймов в секунду
CHUNK = 8000  # кол-во фреймов за один "запрос" к микрофону - тк читаем по кусочкам
FORMAT = pyaudio.paInt16  # глубина звука = 16 бит = 2 байта

engine = pyttsx3.init()


# Чтобы использовать PyAudio, сначала создаем экземпляр PyAudio, который получит
# системные ресурсы для PortAudio (короче подключаемся к микрофону)
py_audio = pyaudio.PyAudio()
# Открываем поток для чтения (input=True) данных с микрофона по-умолчанию и задаем параметры
stream = py_audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
rec = KaldiRecognizer(word.MODEL_VOSK, 16000)

# Большинство команд к другу касаются плеера, поэтому он должен быть всегда доступен
vlc_instance = vlc.Instance()
media_list_player = vlc_instance.media_list_player_new()

len_playlist = 0


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
        if line[0] == '#':
            continue
        elif line[0:5] == 'file:':
            media_path = os.path.abspath(line[8:].rstrip())
            if os.path.isfile(media_path):
                playlist_list.append(media_path)
        elif line[0:6] == 'https:':
            playlist_list.append(line.rstrip())
        else:
            media_path = os.path.abspath(line.rstrip())
            if os.path.isfile(media_path):
                playlist_list.append(media_path)

    # end_of_list.mp3 нужен, чтобы сообщить пользователю о конце плейлиста и чтобы
    # не попасть в бесконечный цикл, когда "не медиа файл" последний в плейлисте (см. main() media_list_player.next())
    if len(playlist_list) > 0:
        if not os.path.isfile(word.END_OF_LIST):
            engine.save_to_file(word.USER_NAME + word.PLAYLIST_END, word.END_OF_LIST)
            engine.runAndWait()

        playlist_list.append( word.END_OF_LIST)

        if not os.path.isfile(word.START_OF_LIST):
            engine.save_to_file(word.USER_NAME + word.PLAYLIST_START, word.START_OF_LIST)
            engine.runAndWait()

        playlist_list.insert(0,word.START_OF_LIST)

    return playlist_list


def play_vlc():
    global len_playlist
    # Если плеер уже запущен, но находится в состоянии пауза, то запускаем его (продолжаем играть)
    if media_list_player.get_state() == vlc.State(4):
        media_list_player.pause()
    else:
        # Если плеер еще не запущен - запускаем.
        # При этом создаем новый плейлист и загружаем в него список

        # Плейлист из файла загружаем в список (список, а не кортеж, т.к. планируется добавление в плейлист?)
        # Пока загружается только плейлист из файла с названием my_playlist.m3u
        playlist_list = load_playlist('my_playlist.m3u')

        len_playlist = len(playlist_list)

        # if len(playlist_list) == 0:
        if len_playlist == 0:
            say_text(word.PLAYLIST_EMPTY)
            return

        media_list = vlc_instance.media_list_new()

        for song in playlist_list:
            media_list.add_media(song.rstrip())

        media_list_player.set_media_list(media_list)

        media_list_player.play()


def say_text(text):
    engine.say(text)
    engine.runAndWait()


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
    elif not commands_to_execute.isdisjoint(word.SET_PLAY):
        say_text(word.USER_NAME + word.PLAYER_START)
        print('execute_command(): ', word.PLAYER_START)
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
    stream.stop_stream()
    stream.close()
    py_audio.terminate()
    print('main: Программа закрыта')

def main():
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
            print('main(): result_text: ', result_text.replace("\n", ""), end='\n')

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

            # vlc.State(6) (Ended) может быть или если список закончился или если файл не воспроизводится (не медиа формат)
            if media_list_player.get_state() == vlc.State(6):
                media_player = media_list_player.get_media_player()

                # Если воспроизведение еще не началось, то это не медиа файл
                if media_player.get_position() == 0:
                    media_list_player.next()

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
