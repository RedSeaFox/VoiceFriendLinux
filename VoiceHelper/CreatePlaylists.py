import os
# import voicehelper_friend_config as word

def create_playlist(name_path):
    print('создаем плейлисты')
    type_media = {'.mp4', '.mp3', '.webm', '.MP3'}
    # subdir = [entry.name for entry in os.scandir(name_path) if entry.is_dir()]
    subdir = [entry for entry in os.scandir(name_path) if entry.is_dir()]
    for d in subdir:
        # files = [entry for entry in os.scandir(dir_audio) if entry.is_file()]
        files = [entry for entry in os.scandir(d.path) if entry.is_file()]
        # files = [entry for entry in os.scandir(d.path) if entry.is_file() and entry.name.endswith()]
       # сооздаем файл плейлиста с именем d.name
        print('создаем плейлист', d.name)
        for f in files:
            # n = f.name
            # # f.name.endswith('.mp4')
            # f.stat()
            # os.path.splitext(f)[1]
            if os.path.splitext(f)[1] in type_media:
                print('Добавим', f.name, 'в плейлист', d.name)





# print('Этот скрипт создает плейлисты и записывает их в каталог', word.DIR_PLAYLIST)
print('Вам будет предложено указать каталог в котором расположены аудиофайлы.')
print('Если в этом каталоге нет вложенных каталогов, то будет создан один плейлист с названием микс')
print('Если в указанном вами каталоге есть вложенные каталоги, то для каждого вложенного каталога будет создан плейлист ')
print('с названием, как у этого вложенного каталога и с аудиофайлами из этого вложенного каталога.')
# print('Вы можете сразу дать имена вложенным каталогам из одного слова, или переименовать плейлисты после создания')
print('Название плейлиста должно состоять из одного слова')
print('Вы можете сразу дать имена вложенным каталогам из одного слова, или переименовать плейлисты после создания', end="\n\n")
# print('')

s = {'q','Q', 'й', 'Й'}

# print('Для выхода из программы нажмите q (или Q) и Enter')
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

        # files = [entry.name for entry in os.scandir(dir_audio) if entry.is_file()]
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

#
# if os.path.isfile(name_file):
#     f = open(name_file)
#     s = f.read()
# else:
#     f = open(name_file, 'w')
#     s = word.PlAYLIST_BY_DEFAULT
#     f.write(s)
#
# f.close()

# *****************************

# Получаем все плейлисты из каталога
# home_dir = os.path.expanduser('~')

# dir_playlst = os.path.expanduser('~') + '/' + word.DIR_PLAYLIST
#
# # Сначала проверяем есть ли каталог с плейлистами
# if os.path.isdir(dir_playlst):
#     print('есть такой каталогю Выводим список')
#     list_of_file = os.listdir(dir_playlst)
#     print(list_of_file)
# else:
#     print('нет такого каталога.Сообщаем пользоателю.')


