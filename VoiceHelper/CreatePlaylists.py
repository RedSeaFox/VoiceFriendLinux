import os
from datetime import datetime

name_dir_playlist = 'VoiceFriend_PlayLists'

def create_playlist(name_path):
    type_media = {'.mp3','.MP3', '.mp4', '.MP4', '.webm', '.WEBM','.wmv', '.WMF', '.mmg','.MPG', '.mp2', '.MP2','.rm',
                  '.RM','.m4a', 'M4A','.ra', 'RA', '.wav','.WAV', '.avi', '.AVI','.flv', '.FLV','.3MP','.wma', '.WMA'}
    # Имя каталога с плейлистами
    dir_home = os.path.expanduser("~")
    # Каталог с плейлистами должен находится в домашнем каталоге
    dir_playlist = dir_home + '/' + name_dir_playlist
    if not os.path.isdir(dir_playlist):
        os.makedirs(dir_playlist)

    name_playlist_mix = 'микс'

    # Сначала создаем плейлисты по вложенным каталогам
    subdir = [entry for entry in os.scandir(name_path) if entry.is_dir()]
    for d in subdir:
        # Сначала провери, вохможно плейлист с таким именем уже существует, тогда добавим к имени создаваемого плейлиста дату
        # os.path.isfile(dir_playlist + '/' + d.name)
        name_playlist = dir_playlist + '/' + d.name + '.m3u'
        if os.path.isfile(name_playlist):
            print('Плейлист', name_playlist, 'уже существует в каталоге', dir_playlist, ', поэтому')
            name_playlist = name_playlist + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            print('в каталоге ', dir_playlist, 'будет создан плейлист ', name_playlist)

        files = [entry for entry in os.scandir(d.path) if entry.is_file()]
        # playlist_file = open(name_playlist, 'w')
        with open(name_playlist, 'w') as playlist_file:
            for f in files:
                # n = f.name
                # # f.name.endswith('.mp4')
                # f.stat()
                # os.path.splitext(f)[1]
                if os.path.splitext(f)[1] in type_media:
                    playlist_file.write(f.path + '\n')
                    # print('Добавим', f.name, 'в плейлист', d.name)

    # Если в каталоге с медиа есть файлы не только в подкаталогах, но и в корне, то для них тоже создаем плейлист
    files = [entry for entry in os.scandir(name_path) if entry.is_file()]
    # playlist_file = open(name_playlist, 'w')
    with open(name_playlist_mix, 'w') as playlist_file:
        for f in files:
            if os.path.splitext(f)[1] in type_media:
                playlist_file.write(f.path + '\n')


print('Этот скрипт создает плейлисты и записывает их в каталог', name_dir_playlist)
print('Вам будет предложено указать каталог в котором расположены аудиофайлы.')
print('Если в этом каталоге нет вложенных каталогов, то будет создан один плейлист с названием микс')
print('Если в указанном вами каталоге есть вложенные каталоги, то для каждого вложенного каталога будет создан плейлист ')
print('с названием, как у этого вложенного каталога и с аудиофайлами из этого вложенного каталога.')
print('Название плейлиста должно состоять из одного слова')
print('Вы можете сразу дать имена вложенным каталогам из одного слова, или переименовать плейлисты после создания', end="\n\n")

s = {'q','Q', 'й', 'Й'}

answ = input('Для выхода из программы нажмите q (или Q) и Enter, если согласны создать плейлисты просто нажмите Enter  ')
print()

q = True if answ in s else False

while not q:
    dir_audio = input('Введите путь к каталогу с аудиофайлами ')

    # Сначала проверяем существует ли введенный пользователем каталог
    if os.path.isdir(dir_audio):

        subdir = [entry.name for entry in os.scandir(dir_audio) if entry.is_dir()]
        if len(subdir) > 0:
            print('В указанном каталоге есть подкаталоги. Из этих подкаталогов будет попытка создать плейлисты: ', subdir)

        files = [entry for entry in os.scandir(dir_audio) if entry.is_file()]
        if len(files) > 0:
            print('В указанном каталоге есть файлы. Из этих файлов будет попытка создать плейлист с именем микс ')
            # print('Будет попытка создать плейлисты из файлов ', files)

        answ = input('Для выхода из программы нажмите q (или Q) и Enter, если согласны создать плейлисты просто нажмите Enter  ')
        q = True if answ in s else False
        if not q:
            create_playlist(dir_audio)

        q = True

    else:
        print('Введенного вами каталога не существует')
        answ = input('Для выхода из программы нажмите q (или Q) и Enter, если хотите ввести имя каталога еще раз просто нажмите Enter  ')
        q = True if answ in s else False
        print()


print('Вышли из программы')



