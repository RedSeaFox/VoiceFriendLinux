import os.path
# import voicehelper_friend_config as word

def create_playlist(path):
    print()

# print('Этот скрипт создает плейлисты и записывает их в каталог', word.DIR_PLAYLIST)
print('Вам будет предложено указать каталог в котором расположены аудиофайлы.')
print('Если в этом каталоге нет вложенных каталогов, то будет создан один плейлист с названием Плейлист')
print('Если в указанном вами каталоге есть вложенные каталоги, то для каждого вложенного каталога будет создан плейлист ')
print('с названием, как у этого вложенного каталога и с аудиофайлами из этого вложенного каталога.')
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
    # print(dir_audio)
    # print()

    # Сначала проверяем существует ли введенный пользователем каталог
    if os.path.isdir(dir_audio):
        print('Есть такой каталог.')
        print('Будет попытка создать плейлисты ', os.listdir(dir_audio))
        # print('Для выхода из программы нажмите q (или Q) и Enter')
        answ = input('Для выхода из программы нажмите q (или Q) и Enter, если согласны создать плейлисты просто нажмите Enter  ')
        q = True if answ in s else False
        if not q:
            create_playlist(dir_audio)
            print('создаем плейлист')
        # list_of_file = os.listdir(dir_audio)
        # print(list_of_file)
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