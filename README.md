# Voice helper friend
<details>
<summary>English</summary>

### About the program
The program is designed for situations where there is no possibility or desire to control a computer with a mouse or keyboard. The program can work offline, since the Vosk offline library is used for speech recognition.

The main purpose of the program is listening or watching media. 

It is also planned to add:
1. Compilation of text files (to-do list, reminders, some information that needs to be recorded)
2. Start the timer 
3. Getting time information
4. Getting weather information.

To determine that the program is being accessed, there is a special word in the program-a beacon. It is declared in the module `voicehelper_friend_config.py`. For example, it can be the word *"friend"*:
``` python
 FRIEND = 'friend'
```
You can redefine the beacon word.

Russian is set by default in the program and, accordingly, the word-beacon is used by default in Russian (*"друг"*) and the username is also indicated in Russian (*"Люся"*). How to set the program up to work with English and other languages, see below.

Management is carried out according to two scenarios.

**The first scenario**: The program constantly listens to incoming words in portions of 2 seconds.  If the program detects an appeal to it in words (a beacon word), then it selects all the words that entered the interval of 2 seconds along with the beacon word and tries to find the correspondence of these words to the commands that it can execute. If such a match is found, the program executes a command from the match. If such a match is not found, the program proceeds to the second scenario.
That is, the main purpose of the first scenario is to catch an appeal to a *"friend"* (the word is a beacon) and, if possible, execute the command. Therefore, the response in the first scenario is fast.

In the **second scenario** listening continues until the pause between words is more than 2-4 seconds or the message length is more than 100 characters. Next, the program also look for the correspondence of the words from the expression to the commands that the program can execute.
That is, in the second scenario, the program has already realized that it has been contacted and that the command may be quite long and that the user may not say this command very quickly. Therefore, the reaction in the second scenario is not very fast.

For commands that the program can execute, in the file `voicehelper_friend_config.py` sets with corresponding sets of words are defined. The names of sets with commands have the form `SET_NAME_OF_COMMAND`. You can redefine the words that commands are called with.  

So in the first release, the program is able to:
1. **Launch the player.**
This can be done using the words listed in the `SET_PLAY` set of the module `voicehelper_friend_config.py` . By default, this set includes the words: *'play', 'sing'*. That is, to start the player, you need to contact a *"friend"* and then say, for example, *"Play"*.

2. **Go to the next and previous track.**  
This can be done using the words listed in the sets `SET_NEXT` and `SET_PREVIOUS` of the module `voicehelper_friend_config.py `. By default, these sets include the words: *'next'* and *'previous'*.

3. **Go to the track with the specified index in the playlist.**  
The set `SET_GOTO` of the module`voicehelper_friend_config.py ` is used for this . By default, this set includes the words: *'go', 'move', 'number'*. You also need to specify that the transition is carried out by tracks.  For this, the `SET_MEASURE_TRACK` set of the module is used `voicehelper_friend_config.py `. By default, this set includes the words: *'track', 'song'*. You also need to specify a number in the command.  
For example.  
First we say the word *friend*. The program understands that it has been contacted. Then we say *"Go to on track five"* or *"Go to song five"*.

5. **Jump inside the track by the specified time.**  
For example, with such a phrase: *"Go to the second five"*. To do this, the sets `SET_GOTO, SET_MEASURE_SECOND, SET_MEASURE_MINUTE, SET_MEASURE_HOUR` of the module are used `voicehelper_friend_config.py `. You can specify seconds, minutes, and hours. So far, only time is recognized, either in seconds, minutes, or hours. That is, if you say 2 minutes and 6 seconds, then the program recognizes this time as 8 seconds. In such cases, you can convert the time to seconds or minutes. For example, instead of 2 minutes and 6 seconds, say 126 seconds.  

5. **Fast-forward/rewind through tracks or seconds/minutes/hours**.  
For example, there may be such commands *"Forward 3 tracks", "Back 2 minutes"*. To do this, the sets `SET_FORWARD, SET_BACK, SET_MEASURE_TRACK, SET_MEASURE_SECOND, SET_MEASURE_MINUTE, SET_MEASURE_HOUR` of the module are used `voicehelper_friend_config.py `. 
It is possible to jump after several tracks (for example, two tracks) or after several seconds/minutes/hours (for example, 20 seconds). So far, only time is recognized, either in seconds, minutes, or hours. That is, the time of 2 minutes and 6 seconds will be recognized as 8 seconds 
By default, the `SET_FORWARD` set includes the word: *'forward'*. The `SET_BACK` set includes the word *'back'*. The sets `SET_MEASURE_SECOND, SET_MEASURE_MINUTE, SET_MEASURE_HOUR` contain the words *'second', 'minute', 'hour'*. The `SET_MEASURE_TRACK` set includes the words: *'track', 'song'*.


At this stage, a single playlist named `my_playlist.m3u` is used, which is currently compiled in advance by "hands" (using the keyboard and mouse). You can create a playlist in the VLC media player program. The playlist looks something like this:
```
#EXTM3U
#EXTINF:2,Kipling_If.mp3
file:///F:/MyMusic/Kipling_If.mp3
#EXTINF:5,Romeo_and_Juliet.mp3
file:///F:/MyMusic/Romeo_and_Juliet.mp3
#EXTINF:5,Waltz.mp3
file:///F:/MyMusic/Waltz.mp3
#EXTINF:10,Bella_ciao.mp3
file:///F:/MyMusic/Bella_ciao.mp3
```


Since the user can express the same command in different words and since the recognition module does not always accurately recognize the endings of words, the program sets different call options for some commands.
For example, the following words can be used to launch the player: *play, sing*. It is written in the module `voicehelper_friend_config.py `:
```python
SET_PLAY = {'play', 'sing'}
```

At this stage, the program runs under Windows. Tested on Windows 10. 
The program code contains outputs (print) for debugging. Some of them are commented out, but if desired, they can be commented out.

### Technology stack
The program is developed in Python 3.11  

The list of all modules and packages required for the correct operation of the program is contained in the file `requirements.txt `.


The offline library [vosk](https://alphacephei.com/vosk/) is used for speech recognition  and its [models](https://alphacephei.com/vosk/models):  *vosk-model-small-en-us-0.15* and *vosk-model-small-ru-0.22*.  
In the first release, the program works with Russian and English. You can add your own language.
To do this, you need to:
1. Download the lightweight language model  [from here](https://alphacephei.com/vosk/models ) and unpack it into the program folder
2. in the module `voicehelper_friend_config.py ` specify the language and add the `elif` block in which to fill in the constants.


### Installation Instructions
Python 3.11 must be installed. Perhaps the program will work on other versions of Python 3. 

Download and place files in a separate folder `voicehelper_friend.py ` and `voicehelper_friend_config.py `. 

Download lightweight libraries **vosk** `vosk-model-small-en-us-0.*` for management in English and `vosk-model-small-ru-0.*` for management in Russian. The program was tested with the libraries `vosk-model-small-en-us-0.15` and `vosk-model-small-ru-0.22`. But the program should also work with other versions of lightweight  libraries. Libraries can be taken from this repository from folder [VoiceHelper](https://github.com/RedSeaFox/voice_friend/tree/master/VoiceHelper) or from the developer's website https://alphacephei.com/vosk/models . Libraries should also be placed in the program folder.

Set up a virtual environment. Take the dependencies from the file `requirements.txt `.

In "VLC media player" create a playlist named `my_playlist.m3u`.  
The playlist must contain the full path to the media files, indicating the disk and folders.  
Example: `file:///F:/MyMusic/Romeo_and_Juliet.mp3`. 

That is, the folder structure should be something like this:  
![file_structure](/image/file_structure.jpg)

The program is started by the file ``voicehelper_friend.py ``. 
The program settings are located in the module `voicehelper_friend_config.py `.

In the module `voicehelper_friend_config.py ` specify the language and name of the user who will communicate with the program.
For example, for the Russian language:  
```python
LANGUAGE = 'ru'
USER_NAME = 'Lucy'
```
For example, for English:  
```python
LANGUAGE = 'en'
USER_NAME = 'Lucy'
```


### Instructions for use
In order for the program to execute commands, you need to contact a *"friend"* and say the commands.  
For example:
1. Say the word *"friend"* and if the command is short, then the command. For example, to start the player, you need to say *"Friend play"*. The word *"friend"* and the command can be pronounced several times (if you keep within 2 seconds).
2. If the command is long, then first you need to pronounce the word *"friend"*. (The word *"friend"* can be pronounced several times in a row.) Wait for the program to respond and then say the command. For example *"Go to on track 25"* or *"Forward 70 seconds"*  

Since commands are not always recognized correctly, they can be pronounced several times and in different versions. Say the numbers only once, otherwise they add up. For example, you can say this *"Go to on track 5 go to track"*

### An example of how the program works ###

There is a playlist file named *my_playlist.m3u* in the program folder.  

Run the program (run the file `voicehelper_friend.py` ). At startup, the program informs you that the program is running.  

If we want to **start playing a playlist**, we say: *"friend play"* or  *"friend sing"*.
If the phrase is fully recognized, the player starts.  
If only the word *"friend"* is recognized, then the program asks you to tell her a command. We can pronounce one or more words from the list *SET_PLAY = {'play', 'play', 'sing', 'sing'}*. For example, we can say *"play"* or *"play sing"* or *"play play"*. Then the player will start. 

**To move on to the next track**, we say *"Friend next"*.
If the phrase is fully recognized, the next track will start.  
If only the word *"friend"* is recognized, then the program asks you to tell her a command. Then we should say the word *"next"*. We can pronounce this word several times so that the program recognizes it for sure. For example*"Next next"*.
Similarly, to go to the previous track. 
Similarly, to go to the previous track, we say *"Friend previous"*.   

**To go to track number five**, we say for example *"Friend go to track five"*.
If the phrase is fully recognized, the fifth track will start.  
If only the word *"friend"* is recognized, then the program asks you to tell her a command. Then we say either *"Go to track five"* or *"Go to song five"* or *"track number five"* or *"Go to track five"* etc.  

**To move forward through several tracks** (**fast forward**), say, for example *"Friend forward seven tracks"*. For example, track number 2 is currently playing, then after executing this command, track number 9 (2 + 7 = 9) will start playing. If the phrase is fully recognized, track number 9 will start playing.
If only the word *"friend"* is recognized, then the program asks you to tell her a command. Then we say either *"Forward seven tracks"* or * "Forward seven tracks forward track"*.  
Similarly, for **moving backwards**, we say for example *"Friend back four tracks"* etc.  

To **switch to the second minute in the current track**, we say *"Friend, go to the second minute"*.
If the phrase is fully recognized, the track will start playing from the second minute.  
If only the word *"friend"* is recognized, then the program asks you to tell her a command. Then we say *"Go to the second minute"* etc.  

To **move forward 10 minutes in the current track** (**fast forward**) (for example, playback is currently at 2 minutes, then after executing the command playback will start at the 12th minute), we say *"Friend forward ten minutes"*. 
If the phrase is fully recognized, the track will start playing from the twelfth minute.  
If only the word *"friend"* is recognized, then the program asks you to tell her a command. Then we say  *"Forward ten minutes"* .
Similarly, to move backwards, we say for example *"Friend back for ten seconds"*, etc.

If the program hears the word *"friend"* during playback, the player is paused and the program asks you to say a command.  
If during playback the program hears *"friend"* and some other command that it knows how to execute, then the program executes this command.
</details>


<details>
<summary>Russian</summary>

### О программе
Программа управления голосом для ситуаций, когда нет возможности или желания управлять компьютером при помощи мышки или клавиатуры. Программа может работать офлайн, так как для распознавания речи используется офлайн библиотека Vosk.

Основное назначение программы - прослушивание или просмотр медиа. 

Также планируется добавить:
1. составление текстовых файлов (список дел, напоминания, какая-то информация, которую надо зафиксировать)
2. запуск таймера 
3. получение информации о времени
4. получение информации о погоде.

Чтобы определить, что обращаются к программе, в программе есть специальное слово маячок. Объявляется оно в модуле `voicehelper_friend_config.py` и по умолчанию это слово *"друг"* :
``` python
FRIEND = 'друг'
```
Вы можете переопределить слово-маячок.

Управление осуществляется по двум сценариям.

**Первый сценарий**: программа постоянно прослушивает входящие слова порциями по 2 секунды.  Если программа обнаруживает в словах обращение к ней (слово-маячок), то она отбирает все слова которые вошли в интервал 2 секунд вместе со словом маячком и пытается найти соответствие этих слов командам, которые она умеет выполнять. Если такое соответствие найдено, то программа выполняет команду из соответствия. Если же такое соответствие не найдено, то программа переходит ко второму сценарию.
То есть основная цель первого сценария уловить обращение к «другу» (слово-маячок) и по возможности выполнить команду. Поэтому отклик по первому сценарию быстрый.

Во **втором сценарии** прослушивание идет до тех пор пока пауза между словами не станет больше 2-4 секунд или длина сообщения не станет больше 100 символов. Далее также ищется соответствие слов из выражения командам, которые программа умеет выполнять.
То есть во втором сценарии программа уже поняла, что к ней обратились и что возможно команда будет достаточно длинная и что пользователь может говорить эту команду не очень быстро. Поэтому реакция по второму сценарию не очень быстрая.

Для команд, которые умеет выполнять программа, в файле `voicehelper_friend_config.py` определены множества с соответствующими наборами слов. Имена множеств с командами имеют вид `SET_ИМЯ_КОМАНДЫ`. Вы можете переопределить слова, которыми команды вызываются. 

Так в первом релизе программа умеет:
1. **Запускать плеер.**  
Это можно сделать при помощи слов перечисленных во множестве `SET_PLAY` модуля `voicehelper_friend_config.py`. По умолчанию, в это множество входят слова: *'играй', 'играть', 'пой', 'петь'*. То есть, чтобы запустить плеер надо обратиться к "другу" и затем сказать например "*Играй*"

2. **Переходить к следующему и предыдущему треку.**  
Это можно сделать при помощи слов перечисленных во множествах `SET_NEXT` и S`ET_PREVIOUS` модуля `voicehelper_friend_config.py`. По умолчанию, в эти множества входят слова: *'следующий'* и *'предыдущий'*.
3. **Переходить к треку с указанным индексом в плейлисте.**  
Для этого используется множество `SET_GOTO` модуля `voicehelper_friend_config.py`. По умолчанию, в это множество входят слова: *'иди', 'перейди', 'включи'*. Также надо указать, что переход осуществляется по трекам.  Для этого используется множество `SET_MEASURE_TRACK` модуля `voicehelper_friend_config.py`. По умолчанию, в это множество входят слова: *'трек', 'песня'*. Также в команде надо указать число.  
Например.  
Сначала говорим слово *друг*. Программа понимает, что обратились к ней. Потом говорим *"Включи трек пять"* или *"Перейди к песне пять"*
4. **Переходить внутри трека к указанному времени.**  
Например, такой фразой: *"Иди к пятой секунде"* или *"Перейди к пятой секунде" или "Включи пятую секунду"*. Для этого используются множества `SET_GOTO, SET_MEASURE_SECOND, SET_MEASURE_MINUTE, SET_MEASURE_HOUR`  модуля `voicehelper_friend_config.py`. Указывать можно секунды, минуты, часы. Пока распознается только время или в секундах, или в минутах, или в часах. То есть если сказать 2 минуты 6 секунд, то программа распознает это время как 8 секунд. В таких случаях можно переводить время в секунды или минуты. Например, вместо 2 минуты 6 секунд  сказать 126 секунд.  
5. **Быстрая перемотка назад/вперед через треки или секунды/минуты/часы**.  
Например могут быть такие команды *"Вперед на три трека", "Назад на две минуты"*. Для этого используются множества `SET_FORWARD, SET_BACK, SET_MEASURE_TRACK, SET_MEASURE_SECOND, SET_MEASURE_MINUTE, SET_MEASURE_HOUR`  модуля `voicehelper_friend_config.py`. 
Возможен прыжок через несколько треков (например два трека) или через несколько секунд/минут/часов (например 20 секунд). Пока распознается только время или в секундах, или в минутах, или в часах. То есть время 2 минуты 6 секунд будет распознано как 8 секунд 
По умолчанию, в множество `SET_FORWARD` входит слово: *'вперёд'*. Во множество `SET_BACK` входит слово *'назад'*. Множества `SET_MEASURE_SECOND, SET_MEASURE_MINUTE, SET_MEASURE_HOUR` содержат слова *'секунда', 'минута', 'час'*. Во множество `SET_MEASURE_TRACK` входят слова: *'трек', 'песня'*.


На данном этапе используется единственный плейлист с именем `my_playlist.m3u`, который пока составляется заранее "руками" ( с помощью клавиатуры и мышки). Плейлист можно составить в программе "VLC media player". Выглядит плейлист примерно так:
```
#EXTM3U
#EXTINF:2,Kipling_If.mp3
file:///F:/MyMusic/Kipling_If.mp3
#EXTINF:5,Romeo_and_Juliet.mp3
file:///F:/MyMusic/Romeo_and_Juliet.mp3
#EXTINF:5,Waltz.mp3
file:///F:/MyMusic/Waltz.mp3
#EXTINF:10,Bella_ciao.mp3
file:///F:/MyMusic/Bella_ciao.mp3
```

Так как одну и ту же команду пользователь может выразить разными словами и так как модуль распознавания не всегда точно распознает окончания слов, в программе для некоторых команд задаются различные варианты вызова.
Так например для запуска плеера могут использоваться такие слова: *играй, играть, пой, петь*. Это прописано в модуле `voicehelper_friend_config.py`:
``` 
SET_PLAY = {'играй', 'играть', 'пой', 'петь'}
```

На данном этапе программа работает под Windows. Тестировалась на Windows 10. 
В коде программы вставлены выводы (print) для отладки и для того чтобы понимать как распознана  ваша речь. Часть print-ов закомментирована, но при желании, их можно раскомментировать.

### Стек технологий
Программа разработана на Python 3.11  

Перечень всех модулей и пакетов, необходимых для корректной работы программы содержаться в файле `requirements.txt`.


Для распознавания речи используется офлайн библиотека [Vosk](https://alphacephei.com/vosk/) и ее малые (Lightweight) [модели](https://alphacephei.com/vosk/models ): *vosk-model-small-en-us-0.15* и *vosk-model-small-ru-0.22*.  
В первом релизе программа работает с русским и английским языком. Вы можете добавить свой язык.
Для этого надо:
1. скачать малую языковую модель (Lightweight)  [отсюда](https://alphacephei.com/vosk/models) и распаковать ее в папку с программой
2. в модуле `voicehelper_friend_config.py` указать язык и добавить блок `elif`, в котором заполнить константы.


### Инструкция по установке
Должен быть установлен Python 3.11. Возможно программа будет работать и на других версиях Python 3. 

Скачать с репозитория из папки [VoiceHelper](https://github.com/RedSeaFox/voice_friend/tree/master/VoiceHelper) и поместить в отдельную папку файлы `voicehelper_friend.py` и `voicehelper_friend_config.py`. 

Скачать малые (Lightweight) библиотеки **vosk** `vosk-model-small-en-us-0.*` для управления на английском языке и `vosk-model-small-ru-0.*` для управления на русском языке. Программа тестировалась с библиотеками `vosk-model-small-en-us-0.15` и `vosk-model-small-ru-0.22`. Но с другими версиями малых библиотек программа также должна работать. Библиотеки можно взять с этого репозитория из папки [VoiceHelper](https://github.com/RedSeaFox/voice_friend/tree/master/VoiceHelper) или с сайта разработчика https://alphacephei.com/vosk/models. Библиотеки надо поместить в папку с программой.

Настроить виртуальное окружение. Зависимости взять из файла `requirements.txt`.

В "VLC media player" создать плейлист с именем `my_playlist.m3u`.  
В плейлисте должен быть прописан полный путь к медиафайлам, с указанием диска и папок.  
Пример: `file:///F:/MyMusic/Romeo_and_Juliet.mp3`. 

То есть структура папки должна быть примерно такая:  
![file_structure](/image/file_structure.jpg)

Программа запускается файлом ```voicehelper_friend.py```. 
Настройки программы находятся в модуле `voicehelper_friend_config.py`.

В модуле `voicehelper_friend_config.py` указать язык и имя пользователя, который будет общаться с программой.
Например, для русского языка:  
```python
LANGUAGE = 'ru'
USER_NAME = 'Люся'
```
Например, для английского языка:  
```python
LANGUAGE = 'en'
USER_NAME = 'Lucy'
``` 

### Инструкция по использованию
Чтобы программа выполнила команды, надо обратиться к *"другу"* и произнести команды.  
Например:
1. произнести слово *"друг"* и если команда короткая, то команду. Например, чтобы запустить плеер, надо произнести *"Друг играй"*. Слово *"друг"* и команду можно произносить несколько раз (если уложитесь в 2 секунды).
2. Если команда длинная, то сначала надо произнести слово *"друг"*. (Слово *"друг"* можно произносить несколько раз подряд.) Дождаться отклика программы и потом произнести команду. Например *"Включи трек 25"* или *"Вперед на 70 секунд"*  

Так как команды распознаются не всегда корректно, то их можно произносить по несколько раз и в разных вариантах. Числа произносить только один раз, иначе они суммируются. Например можно сказать так *"Включи трек пять перейди к треку"*


### Пример работы программы ###

В папке с программой есть файл плейлиста с именем `my_playlist.m3u`.  

Запускаем программу (запускаем файл`voicehelper_friend.py`). При запуске программа сообщает, что программа запущена.  

Если хотим **запустить воспроизведение плейлиста**, то говорим: *"друг играй"* или *"друг пой"*.
Если фраза распознана полностью, то запускается плеер.  
Если распознано только слово *"друг"*, то программа просит сказать ей команду. Можем произнести одно или несколько слов из списка  *SET_PLAY = {'играй', 'играть', 'пой', 'петь'}*. Например, можем сказать *"пой, играй, пой"*. Тогда запуститься плеер.  

Чтобы **перейти к следующему треку**, говорим *"Друг следующий"*.
Если фраза распознана полностью, то запустится следующий трек.  
Если распознано только слово *"друг"*, то программа просит сказать ей команду. Тогда говорим слово *"следующий"*. Можем произнести это слово несколько раз, чтобы программа распознала его наверняка. Например*"Следующий следующий"*.  
Аналогично для перехода к предыдущему треку говорим *"Друг предыдущий"*.  

Чтобы **перейти к треку номер пять**, то говорим например *"Друг включи трек пять"*.
Если фраза распознана полностью, то запустится пятый трек.  
Если распознано только слово *"друг"*, то программа просит сказать ей команду. Тогда говорим или *"Включи трек пять"* или *"Перейди к песне пять"* или *"Включи пятый трек"* или *"Перейди к пятому треку"* и т.д.  

Чтобы **перейти через несколько треков вперед** (**быстрая перемотка вперед**), говорим, например *"Друг вперед на семь треков"*. Например, сейчас воспроизводится трек номер 2 , то после выполнения этой команды начнет воспроизводиться трек номер 9 (2 + 7 = 9). Если фраза распознана полностью, то начнет воспроизводиться трек номер 9.  
Если распознано только слово *"друг"*, то программа просит сказать ей команду. Тогда говорим или *"Вперед на семь треков"* или *"Вперед на семь треков вперед трек"*.  
Аналогично для **передвижения назад**, говорим например *"Друг назад на четыре трека"* и т.д.

Чтобы **в текущем треке перейти ко второй минуте**, говорим *"Друг включи вторую минуту"*.
Если фраза распознана полностью, то трек начнет воспроизводиться со второй минуты.  
Если распознано только слово *"друг"*, то программа просит сказать ей команду. Тогда говорим или *"Включи вторую минуту"* или *"Перейди ко второй минуте"* и т.д.  

Чтобы **в текущем треке передвинуться на 10 минут вперед** (**быстрая перемотка вперед**) (например, сейчас воспроизведение на отметке 2 минуты, то после выполнения команды воспроизведение начнется с 12-ой минуты), говорим *"Друг вперед на десять минут"*. 
Если фраза распознана полностью, то трек начнет воспроизводиться с двенадцатой минуты.  
Если распознано только слово *"друг"*, то программа просит сказать ей команду. Тогда говорим или *"Вперед на десять минут"* или *"Вперед на десять минут вперед"*.
Аналогично для передвижения назад, говорим например *"Друг назад на десять секунд"* и т.д.  

Если во время воспроизведения программа услышит слово *"друг"*, то **плеер ставится на паузу** и программа просит произнести команду.  
Если во время воспроизведения программа услышит *"друг"* и еще какую-то команду, которую она умеет выполнять, то программы выполнит эту команду.  


</details>