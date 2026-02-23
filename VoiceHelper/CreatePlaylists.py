import os
from datetime import datetime

from tkinter import *
from tkinter import  ttk
from tkinter.scrolledtext import ScrolledText

name_dir_playlist = 'VoiceFriend_PlayLists'

def creating(name_path):
    type_media = {'.mp3', '.MP3', '.mp4', '.MP4', '.webm', '.WEBM', '.wmv', '.WMF', '.mmg', '.MPG', '.mp2', '.MP2',
                  '.rm',
                  '.RM', '.m4a', 'M4A', '.ra', 'RA', '.wav', '.WAV', '.avi', '.AVI', '.flv', '.FLV', '.3MP', '.wma',
                  '.WMA'}

    # Имя каталога с плейлистами
    dir_home = os.path.expanduser("~")
    # Каталог с плейлистами должен находится в домашнем каталоге
    dir_playlist = dir_home + '/' + name_dir_playlist
    if not os.path.isdir(dir_playlist):
        os.makedirs(dir_playlist)

    name_playlist_mix = 'микс'
    new_playlist = list()

    # Сначала создаем плейлисты по вложенным каталогам
    subdir = [entry for entry in os.scandir(name_path) if entry.is_dir()]
    for d in subdir:
        # Сначала проверим, возможно плейлист с таким именем уже существует, тогда добавим к имени создаваемого плейлиста дату
        name_playlist = dir_playlist + '/' + d.name + '.m3u'
        if os.path.isfile(name_playlist):
            name_playlist = dir_playlist + '/' + d.name + '_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.m3u'

        files = [entry for entry in os.scandir(d.path) if entry.is_file()]

        with open(name_playlist, 'w') as playlist_file:
            for f in files:
                if os.path.splitext(f)[1] in type_media:
                    playlist_file.write(f.path + '\n')

        new_playlist.append(name_playlist)

    # Если в каталоге с медиа есть файлы не только в подкаталогах, но и в корне, то для них тоже создаем плейлист
    files = [entry for entry in os.scandir(name_path) if entry.is_file()]
    if len(files) > 0:
        name_playlist = dir_playlist + '/' + name_playlist_mix + '.m3u'
        if os.path.isfile(name_playlist):
            name_playlist = dir_playlist + '/' + name_playlist_mix + '_' + datetime.now().strftime(
                "%Y_%m_%d_%H_%M_%S") + '.m3u'
        with open(name_playlist, 'w') as playlist_file:
            for f in files:
                if os.path.splitext(f)[1] in type_media:
                    playlist_file.write(f.path + '\n')

        new_playlist.append(name_playlist)

    # mess = 'В каталоге ' + name_dir_playlist + ' созданы плейлисты:' + ' \n '.join(new_playlist)
    mess = 'Cозданы плейлисты:\n ' + ' \n '.join(new_playlist)

    return mess


def create_playlist():
    dir_audio = entry_path.get()

    if not os.path.isdir(dir_audio):
        mess_created = 'Указанного каталога не существует'
    else:
        mess_created = creating(dir_audio)

    st_created.configure(state=NORMAL)
    st_created.replace('1.0', END, mess_created)
    st_created.configure(state=DISABLED)


def check_dir():
    st_created.replace('1.0', END, '')

    dir_audio = entry_path.get()# получаем введенный текст
    mess = ''

    if os.path.isdir(dir_audio):

        subdir = [entry.name+'.m3u' for entry in os.scandir(dir_audio) if entry.is_dir()]

        if len(subdir) > 0:
            mess = 'В указанном каталоге есть подкаталоги. Из этих подкаталогов будет попытка создать плейлисты с именами: \n' + "\n".join(subdir)

        files = [entry for entry in os.scandir(dir_audio) if entry.is_file()]
        if len(files) > 0:
            mess = mess if mess=='' else mess + '\n'

            mess = mess + 'В указанном каталоге есть файлы. Из этих файлов будет попытка создать плейлист с именем микс '

    else:
        mess = 'Указанного каталога не существует'

    st_check.configure(state=NORMAL)
    st_check.replace('1.0',END, mess)
    st_check.configure(state=DISABLED)


# Основное окно
root = Tk()
root.title("Создание плейлистов")

frame = ttk.Frame()
frame.pack(anchor=NW, fill=X, padx=10, pady=10)

label_help = ttk.Label(frame, text='Этот скрипт создает плейлисты и записывает их в каталог VoiceFriend_PlayLists в домашнем каталоге\n'
'Плейлисты создаются по медиа-файлам из указанного вами каталога.\n'
'Если в этом каталоге нет вложенных каталогов, то будет создан один плейлист с названием микс.\n'
'Если в указанном вами каталоге есть вложенные каталоги, то для каждого вложенного каталога будет создан плейлист\n'
'с названием, как у этого вложенного каталога и с аудиофайлами из этого вложенного каталога.\n'
'Если в каталоге VoiceFriend_PlayLists уже существуют плейлисты с именами совпадающими с создаваемыми, то\n'
'к именам создаваемых плейлистов будет добавлено время.\n'
'Для того чтобы использовать плейлисты в программе VoiceFriendLinux, название плейлиста должно состоять из одного слова.\n'
'При необходимости скорректируйте названия плейлистов после создания.\n',justify = "left")
label_help.pack()

# Область "Ввести путь"
frame_path = ttk.Frame(frame)
frame_path.pack(anchor=NW, fill=X)

label_path = ttk.Label( frame_path, text="Введите путь к каталогу с аудиофайлами")
label_path.pack(anchor=NW)

entry_path = ttk.Entry( frame_path)
entry_path.pack(anchor=NW, fill=X)

# Область "Проверить каталог"
frame_check = ttk.Frame(frame)
frame_check.pack(anchor=NW, fill=X)

btn_continue = ttk.Button( frame_check, text="Проверить каталог", command=check_dir)
btn_continue.pack(anchor=NW, padx=6, pady=6)

st_check = ScrolledText( frame_check, height=5, wrap='word', background=root['bg'], borderwidth=0.5, state=DISABLED)
st_check.pack(fill=BOTH, side=LEFT, expand=True)

# Область "Создать плейлисты"
frame_create = ttk.Frame(frame)
frame_create.pack(anchor=NW, fill=X)

btn_create = ttk.Button(frame_create, text="Создать плейлисты", command=create_playlist)
btn_create.pack(anchor=NW, padx=6, pady=6)

st_created = ScrolledText( frame_create, height=5, wrap='word', background=root['bg'], borderwidth=0.5, state=DISABLED)
st_created.pack(fill=BOTH, side=LEFT, expand=True)

root.mainloop()


