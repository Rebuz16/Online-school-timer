# -*- coding: utf-8 -*-
"""
Виртуальный микрофон с таймером уроков.
=========================================

Что делает скрипт
------------------
1. Создаёт "маршрутизатор" аудио, который выводит звук в виртуальный
   микрофон (VB-Audio Virtual Cable или аналог) и одновременно в
   реальные динамики.
2. Ваш физический микрофон попадает в виртуальный микрофон ТОЛЬКО пока
   зажата клавиша Alt (режим "рации").
3. По расписанию уроков (уроки по 40 минут) озвучивает:
     - начало урока: звук sounds/start.mp3 + голосом "Урок номер N";
     - конец урока: звук sounds/stop.mp3 (без объявления номера);
     - остаток времени за 15, 10, 5 и 1 минуту до конца урока голосом
       (Google Text-to-Speech, украинский язык, с правильными
       окончаниями числительных: "1 хвилина", "2 хвилини", "5 хвилин").
   Звук идёт и в виртуальный микрофон, и в динамики.
3а. Автоматически проверяет воздушную тревогу в місті Києві через
    публичное API alerts.in.ua и озвучивает:
      - начало тревоги: sounds/alarm.mp3 + "Увага! В місті Києві
        оголошена повітряна тривога!" - ЗАМЕТНО ГРОМЧЕ всех остальных
        оповещений (AIR_RAID_VOLUME_GAIN);
      - відбій: "Відбій повітряної тривоги" (обычной громкостью).
    Для этого нужен бесплатный токен с https://devs.alerts.in.ua
    (см. AIR_RAID_API_TOKEN в настройках).
4. Показывает поверх всех окон компактный таймер обратного отсчёта
   с номером текущего урока и временем окончания текущего периода.
   Во время перемены таймер переключается в красный цвет.
4а. Тот же таймер можно дополнительно вывести как отдельную
    виртуальную веб-камеру (через pyvirtualcam + драйвер "OBS Virtual
    Camera") - тогда его можно выбрать как обычную камеру в Zoom,
    Discord, Teams и т.п., или добавить как источник в самой OBS.
    Во время воздушной тревоги над таймером на камере мигает (раз в
    секунду) красная надпись "Повітряна тривога!". Экранное окно и
    виртуальная камера включаются/выключаются независимо друг от
    друга константами ENABLE_SCREEN_TIMER и ENABLE_VIRTUAL_CAMERA_TIMER.
4б. Расписание можно задать по-разному для разных дней недели через
    EXCLUDED_LESSONS_BY_WEEKDAY (например, "нулевого урока нет по
    понедельникам", "по субботам и воскресеньям уроков нет вообще").
4в. Когда уроки на сегодня уже закончились (или ещё не начались, и до
    первого урока больше минуты) - окно таймера полностью СКРЫВАЕТСЯ,
    а проверка воздушной тревоги и любые озвучки приостанавливаются:
    в это время скрипт не отправляет вообще никаких запросов на
    сервер. Окно появляется и работа возобновляется ровно за минуту
    до начала первого урока (см. ACTIVE_LEAD_SEC).
5. Ctrl+Alt+R — принудительно озвучить, сколько осталось до конца
   текущего урока/перемены (или до начала следующего урока).
5а. Ctrl+Alt+E — вручную показать/скрыть окно таймера на экране (эта
    ручная настройка не зависит от автоматического режима "сна" из
    пункта 4а - можно скрыть окно даже во время урока и наоборот).
5б. Ctrl+NumpadN — настраиваемые звуковые эффекты из папки sounds/,
    привязка задаётся в NUMPAD_SOUND_BINDINGS (какой файл на какую
    цифру и разово или по кругу). По умолчанию: Ctrl+Numpad2 - разово
    sounds/grasshoppers.mp3; Ctrl+Numpad1 - переключатель тихого
    циклического sounds/wait.mp3 (повторное нажатие останавливает).
    Работает именно с физической цифровой клавиатурой (Numpad), не с
    верхним рядом цифр - см. комментарий у NUMPAD_SOUND_BINDINGS.
5в. Ctrl+Q — аварийная остановка ВООБЩЕ ВСЕХ звуков: обрывает и то,
    что уже играет/в очереди (включая любые циклические привязки из
    NUMPAD_SOUND_BINDINGS), и то, что ещё синтезируется/скачивается в
    фоне (обычная озвучка, тревога, start.mp3/stop.mp3 и т.п.) - оно
    не прозвучит, когда досчитается.
6. Если зажать Ctrl и потянуть окно таймера левой кнопкой мыши —
   окно можно перетащить в любое место экрана.

Звуковые файлы оповещений
--------------------------
Положите в подпапку "sounds" рядом со скриптом файлы:
    sounds/start.mp3 - проигрывается в начале урока (перед фразой "Урок номер N")
    sounds/stop.mp3  - проигрывается в конце урока
    sounds/alarm.mp3 - проигрывается перед фразой о воздушной тревоге
плюс любые файлы, которые вы укажете в NUMPAD_SOUND_BINDINGS для
Ctrl+NumpadN (по умолчанию grasshoppers.mp3 и wait.mp3 - см. настройки).
Если какого-то файла нет - скрипт не упадёт, просто напечатает
предупреждение в консоль и пропустит именно звуковую часть оповещения
(голосовая часть, если она предусмотрена, всё равно озвучится).

Установка перед первым запуском
--------------------------------
1. Установите виртуальное аудио-устройство, например VB-Audio Virtual
   Cable: https://vb-audio.com/Cable/  (после установки в системе
   появится устройство воспроизведения "CABLE Input" и устройство
   записи "CABLE Output").
2. Установите зависимости:
       pip install sounddevice numpy keyboard gTTS
   Дополнительно нужен ffmpeg, установленный в системе и добавленный
   в PATH: https://ffmpeg.org/download.html — он используется для
   декодирования mp3, который отдаёт Google TTS (проверить установку
   можно командой "ffmpeg -version" в консоли).
   ВАЖНО: озвучка через Google TTS (gTTS) требует подключения к
   интернету — без него фразы не озвучатся.
   Если нужна виртуальная камера-таймер (ENABLE_VIRTUAL_CAMERA_TIMER):
       pip install pyvirtualcam pillow
   и установите OBS Studio (https://obsproject.com/) - саму программу
   запускать не обязательно, нужен только её драйвер виртуальной
   камеры. Если при этом в OBS запущена ЕЁ СОБСТВЕННАЯ виртуальная
   камера ("Start Virtual Camera") - будет конфликт за устройство,
   используйте только один источник за раз.
3. Узнайте точные названия ваших аудио-устройств:
       python lesson_mic_timer.py --list-devices
   и подставьте нужные подстроки названий в блок НАСТРОЙКИ ниже
   (REAL_MIC_NAME, VIRTUAL_CABLE_NAME, SPEAKER_NAME).
4. Заполните расписание LESSON_END_TIMES временем окончания уроков.
5. В программе, где нужен виртуальный микрофон (Zoom, Discord, Teams
   и т.п.), выберите в качестве микрофона устройство
   "CABLE Output (VB-Audio Virtual Cable)".
6. Запускайте скрипт от имени администратора (на Windows это нужно,
   чтобы библиотека keyboard могла ловить глобальные горячие клавиши
   и состояние Alt/Ctrl вне зависимости от активного окна).

Запуск:
       python lesson_mic_timer.py
"""

import os
import sys
import time
import json
import tempfile
import threading
import datetime
import subprocess
import urllib.request
import urllib.error

import numpy as np
import sounddevice as sd
from gtts import gTTS
import keyboard
import tkinter as tk


# ================== НАСТРОЙКИ (правьте под себя) ==================

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

# Подстроки названий устройств (регистр не важен). Смотрите точные
# названия командой: python lesson_mic_timer.py --list-devices
REAL_MIC_NAME = "Набор микрофонов (2- Технология Intel® Smart Sound для цифровых микрофонов)"        # ваш физический микрофон
VIRTUAL_CABLE_NAME = "CABLE Input (VB-Audio Virtual Cable)"  # вход виртуального кабеля (туда пишем звук)
SPEAKER_NAME = None                 # None = устройство вывода по умолчанию

# Время ОКОНЧАНИЯ каждого урока за день, формат "ЧЧ:MM".
# Уроки нумеруются с 0 в том порядке, в котором они здесь перечислены.
LESSON_END_TIMES = [
    "12:15",
    "13:05",
    "13:55",
    "14:50",
    "15:45",
    "16:40",
    "17:30",
    "18:15",
]

LESSON_DURATION_MIN = 40   # длительность одного урока в минутах
                            # (перемена = промежуток между концом одного
                            # урока и началом следующего, вычисляется сама)

# Каких уроков (по индексу из LESSON_END_TIMES, начиная с 0) нет в
# конкретный день недели. Ключ - день недели как в datetime.weekday()
# (0=понедельник, 1=вторник, 2=среда, 3=четверг, 4=пятница, 5=субтота,
# 6=воскресенье). Значение - множество индексов уроков без них, либо
# строка "ALL", если в этот день уроков вообще нет.
#   - нулевой урок есть только в среду и четверг;
#   - в четверг нет седьмого урока;
#   - в субботу и воскресенье уроков нет вообще.
EXCLUDED_LESSONS_BY_WEEKDAY = {
    0: {0},      # понедельник - без нулевого урока
    1: {0},      # вторник - без нулевого урока
    2: set(),    # среда - все уроки, включая нулевой
    3: {7},      # четверг - есть нулевой, но нет седьмого
    4: {0},      # пятница - без нулевого урока
    5: "ALL",    # суббота - выходной
    6: "ALL",    # воскресенье - выходной
}

ANNOUNCE_MARKS_MIN = [10, 5, 1]     # за сколько минут до конца озвучивать
HOTKEY_FORCE_ANNOUNCE = "ctrl+alt+r"
HOTKEY_TOGGLE_OVERLAY = "ctrl+alt+e"   # вручную показать/скрыть окно таймера на экране
HOTKEY_STOP_ALL_SOUNDS = "ctrl+q"      # немедленно обрывает вообще все звуки/озвучки

# Ctrl + Numpad N. ВАЖНО: библиотека keyboard по умолчанию не различает
# цифровую клавиатуру (Numpad) и обычный верхний ряд цифр - это её
# собственное ограничение (см. github.com/boppreh/keyboard issue #161).
# Поэтому эти хоткеи ловятся отдельно, низкоуровневым хуком с проверкой
# event.is_keypad (см. register_ctrl_numpad_hotkeys ниже), а не через
# keyboard.add_hotkey. Предполагается, что Num Lock включён - иначе
# физический Numpad присылает имена стрелок/Home/End вместо цифр.
#
# NUMPAD_SOUND_BINDINGS - привязка звуков из папки sounds/ к цифрам
# Numpad (0-9). Ключ - цифра как строка, значение - словарь:
#   "file" - имя mp3-файла в sounds/ (обязательно);
#   "loop" - True: работает как переключатель - первое Ctrl+NumpadN
#            запускает звук по кругу без пауз, повторное - останавливает;
#            False (или не указано): разовое проигрывание при каждом
#            нажатии Ctrl+NumpadN;
#   "gain" - громкость, 1.0 = обычная (необязательно, по умолчанию 1.0;
#            для зацикленных звуков разумно делать потише, см. wait.mp3).
# Можно добавлять/убирать любые цифры и файлы - код ничего не знает про
# конкретные имена файлов, всё берётся из этого словаря.
NUMPAD_SOUND_BINDINGS = {
    "1": {"file": "wait.mp3", "loop": True, "gain": 0.4},
    "2": {"file": "grasshoppers.mp3", "loop": False},
    "3": {"file": "modem.mp3", "loop": False},
}

PTT_KEY = "alt"                      # клавиша "рации"

# Множитель скорости озвучки: 1.0 = обычная скорость gTTS, 1.3 = на 30%
# быстрее (тон голоса не меняется - используется ffmpeg atempo).
TTS_SPEED = 1.3

# Код языка для Google Text-to-Speech ("uk" = украинский).
TTS_LANG = "uk"

# --- "define"-переключатели: поставьте False, чтобы полностью
# отключить соответствующий таймер (ничего не создаётся и не запускается). ---
ENABLE_SCREEN_TIMER = True           # окно таймера на экране (tkinter, поверх всех окон)
ENABLE_VIRTUAL_CAMERA_TIMER = True   # тот же таймер как отдельная виртуальная веб-камера

# Параметры виртуальной камеры (используется библиотекой pyvirtualcam,
# которая на Windows работает через драйвер "OBS Virtual Camera" -
# поэтому должен быть установлен OBS Studio, но саму программу OBS
# запускать не обязательно). Если при этом в самой OBS Studio нажата
# кнопка "Start Virtual Camera" - будет конфликт: устройство может
# отдавать картинку только одному источнику одновременно, так что
# используйте либо это, либо встроенную виртуальную камеру OBS.
VIRTUAL_CAMERA_WIDTH = 640
VIRTUAL_CAMERA_HEIGHT = 360
VIRTUAL_CAMERA_FPS = 15

# Цвета таймера в зависимости от текущего периода
COLOR_LESSON = "#00ff88"    # идёт урок
COLOR_BREAK = "#ff3b3b"     # идёт перемена
COLOR_WAITING = "#ffcc00"   # уроки ещё не начались / уже закончились на сегодня

# Папка со звуковыми файлами оповещений (start.mp3, stop.mp3, alarm.mp3)
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

# --- Воздушная тревога в Києві (alerts.in.ua) ---
# Бесплатный токен получите в личном кабинете https://devs.alerts.in.ua
# Если оставить пустым - функция автоматически отключится (с предупреждением
# в консоли), остальной скрипт продолжит работать как обычно.
AIR_RAID_ENABLED = True
AIR_RAID_API_TOKEN = "f9c4170f684ceeceaefa0e07cdc3678381666da5ab2203"
AIR_RAID_API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"
AIR_RAID_POLL_INTERVAL_SEC = 8
# Точное название Киева в ответе API. На момент написания скрипта
# alerts.in.ua отдаёт город как "м. Київ" отдельно от Київської області -
# если это изменится, проверьте актуальную схему на https://devs.alerts.in.ua
# и поправьте значение здесь.
AIR_RAID_CITY_TITLE = "м. Київ"

# Во сколько раз громче звучит именно оповещение о НАЧАЛЕ воздушной
# тревоги (звук alarm.mp3 + фраза), чтобы оно выделялось на фоне любых
# других оповещений. Отбой тревоги озвучивается обычной громкостью.
AIR_RAID_VOLUME_GAIN = 1.8

# За сколько секунд до начала первого урока показывать окно таймера и
# возобновлять проверку тревоги. Всё время до этого (после конца
# последнего урока и до этого порога перед первым) окно скрыто, а
# проверки тревоги и любые оповещения приостановлены - никаких
# запросов на сервер в это время не отправляется.
ACTIVE_LEAD_SEC = 60

# Как часто (в секундах) скрипт "просыпается", чтобы проверить, не
# пора ли уже показать таймер, пока он скрыт. Не влияет на точность
# самого расписания - только на частоту этой фоновой проверки.
SLEEP_POLL_INTERVAL_SEC = 5

# ====================================================================


# ---------------------------------------------------------------------
# Правильные окончания украинских числительных (1 хвилина, 2 хвилини,
# 5 хвилин и т.п.), чтобы озвучка не звучала как "1 хвилин".
# ---------------------------------------------------------------------

def ukrainian_plural(n: int, one: str, few: str, many: str) -> str:
    """Возвращает форму слова, соответствующую числу n по правилам
    украинского языка: 1 -> one, 2-4 -> few, 0/5-20/... -> many
    (с учётом исключений 11-14)."""
    n_abs = abs(int(n))
    mod10 = n_abs % 10
    mod100 = n_abs % 100
    if mod10 == 1 and mod100 != 11:
        return one
    if 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
        return few
    return many


# ---------------------------------------------------------------------
# Служебные функции для работы с устройствами
# ---------------------------------------------------------------------

def list_devices():
    print(sd.query_devices())


def find_device(name_substr, kind="input"):
    """Ищет индекс устройства по подстроке имени."""
    if not name_substr:
        return None
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if name_substr.lower() in d["name"].lower():
            if kind == "input" and d["max_input_channels"] > 0:
                return i
            if kind == "output" and d["max_output_channels"] > 0:
                return i
    raise RuntimeError(
        f"Устройство, содержащее '{name_substr}', не найдено. "
        f"Запустите со флагом --list-devices, чтобы увидеть список."
    )


# ---------------------------------------------------------------------
# Синтез речи (онлайн, через Google Text-to-Speech)
# ---------------------------------------------------------------------

_tts_lock = threading.Lock()
_tts_cache = {}          # текст -> np.ndarray, чтобы не дёргать сеть повторно
_tts_cache_lock = threading.Lock()


def _atempo_filter_chain(speed: float) -> str:
    """ffmpeg-фильтр atempo меняет темп речи без изменения высоты тона,
    но поддерживает множитель только в диапазоне [0.5, 2.0]. Для выхода
    за эти границы фильтры выстраиваются цепочкой."""
    remaining = speed if speed > 0 else 1.0
    filters = []
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.3f}")
    return ",".join(filters)


def _mp3_to_pcm_via_ffmpeg(mp3_path: str, speed: float = 1.0) -> np.ndarray:
    """Декодирует mp3-файл в float32 mono PCM с частотой SAMPLE_RATE,
    вызывая внешний ffmpeg напрямую (без pydub/audioop). При speed != 1.0
    дополнительно ускоряет/замедляет речь без изменения тона голоса."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", mp3_path,
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
    ]
    if abs(speed - 1.0) > 1e-3:
        cmd += ["-filter:a", _atempo_filter_chain(speed)]
    cmd += ["-f", "s16le", "-"]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg не найден. Установите его и добавьте в PATH: "
            "https://ffmpeg.org/download.html"
        )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg завершился с ошибкой: {result.stderr.decode(errors='ignore')}")

    raw = result.stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def text_to_pcm(text: str) -> np.ndarray:
    """Синтезирует текст через Google TTS и возвращает float32 mono PCM
    с частотой SAMPLE_RATE. Результаты кэшируются по тексту, т.к.
    фразы вроде "15 хвилин до кінця уроку" повторяются каждый урок."""

    with _tts_cache_lock:
        cached = _tts_cache.get(text)
    if cached is not None:
        return cached

    tmp_mp3 = tempfile.mktemp(suffix=".mp3")
    try:
        with _tts_lock:
            tts = gTTS(text=text, lang=TTS_LANG)
            tts.save(tmp_mp3)

        data = _mp3_to_pcm_via_ffmpeg(tmp_mp3, speed=TTS_SPEED)
    except Exception as e:
        print(f"[TTS] Ошибка синтеза речи через Google TTS: {e}. "
              f"Проверьте подключение к интернету и наличие ffmpeg в PATH.")
        data = np.zeros(0, dtype=np.float32)
    finally:
        if os.path.exists(tmp_mp3):
            os.remove(tmp_mp3)

    with _tts_cache_lock:
        _tts_cache[text] = data

    return data


# ---------------------------------------------------------------------
# Звуковые файлы-оповещения (sounds/start.mp3, stop.mp3, alarm.mp3)
# ---------------------------------------------------------------------

_sound_cache = {}
_sound_cache_lock = threading.Lock()


def load_sound(filename: str) -> np.ndarray:
    """Загружает и кэширует звуковой файл из папки SOUNDS_DIR. Если файла
    нет или его не удалось декодировать - возвращает пустой массив
    (тишину) и печатает предупреждение, не прерывая работу скрипта."""
    path = os.path.join(SOUNDS_DIR, filename)

    with _sound_cache_lock:
        cached = _sound_cache.get(path)
    if cached is not None:
        return cached

    if not os.path.exists(path):
        print(f"[SOUND] Файл не найден: {path}. Положите его в папку "
              f"{SOUNDS_DIR} или проверьте имя файла.")
        data = np.zeros(0, dtype=np.float32)
    else:
        try:
            data = _mp3_to_pcm_via_ffmpeg(path, speed=1.0)
        except Exception as e:
            print(f"[SOUND] Не удалось декодировать {path}: {e}")
            data = np.zeros(0, dtype=np.float32)

    with _sound_cache_lock:
        _sound_cache[path] = data

    return data


# ---------------------------------------------------------------------
# Потокобезопасный буфер сэмплов (замена очереди для микширования)
# ---------------------------------------------------------------------

class SampleBuffer:
    def __init__(self):
        self._buf = np.zeros(0, dtype=np.float32)
        self._lock = threading.Lock()

    def write(self, data: np.ndarray):
        with self._lock:
            self._buf = np.concatenate([self._buf, data])

    def read(self, n: int) -> np.ndarray:
        with self._lock:
            have = len(self._buf)
            if have >= n:
                out = self._buf[:n]
                self._buf = self._buf[n:]
            else:
                out = np.pad(self._buf, (0, n - have))
                self._buf = np.zeros(0, dtype=np.float32)
            return out

    def clear(self):
        """Немедленно обрывает всё, что уже лежит в буфере и ждёт вывода."""
        with self._lock:
            self._buf = np.zeros(0, dtype=np.float32)


# ---------------------------------------------------------------------
# Аудио-маршрутизатор: реальный микрофон -> виртуальный микрофон,
# плюс озвучка в виртуальный микрофон и в динамики
# ---------------------------------------------------------------------

class AudioRouter:
    def __init__(self, mic_device, cable_device, speaker_device):
        self.mic_device = mic_device
        self.cable_device = cable_device
        self.speaker_device = speaker_device

        self.mic_buffer = SampleBuffer()          # живой звук с микрофона (PTT)
        self.tts_cable_buffer = SampleBuffer()     # озвучка -> в виртуальный микрофон
        self.tts_speaker_buffer = SampleBuffer()   # озвучка -> в динамики

        self.ptt_active = False  # обновляется отдельным потоком (см. ptt_loop)

        # "Поколение звука": Ctrl+Q увеличивает этот счётчик. Каждая
        # озвучка запоминает текущее поколение при старте и, прежде чем
        # что-то записать в буфер, проверяет, не устарело ли оно - это
        # позволяет обрывать даже те озвучки, которые в момент Ctrl+Q
        # ещё синтезируются в Google TTS или декодируются из mp3 (то
        # есть их ещё нет в буфере, обрыв буфера их не поймал бы).
        self._sound_generation = 0
        self._generation_lock = threading.Lock()

        self._mic_stream = None
        self._cable_stream = None
        self._speaker_stream = None

    def _current_generation(self) -> int:
        with self._generation_lock:
            return self._sound_generation

    def _is_current_generation(self, gen: int) -> bool:
        with self._generation_lock:
            return self._sound_generation == gen

    def stop_all_sounds(self):
        """Ctrl+Q: немедленно обрывает вообще все звуки - и то, что уже
        лежит в буфере и ждёт вывода, и то, что ещё синтезируется/
        декодируется в фоновых потоках (announce/announce_sound) и
        поэтому появилось бы в буфере только через секунду-другую."""
        self.tts_cable_buffer.clear()
        self.tts_speaker_buffer.clear()
        with self._generation_lock:
            self._sound_generation += 1

    # --- захват с реального микрофона ---
    def _mic_callback(self, indata, frames, time_info, status):
        if self.ptt_active:
            frame = indata[:, 0] if indata.ndim > 1 else indata
            self.mic_buffer.write(frame.copy())
        # если рация не нажата - просто ничего не пишем в буфер,
        # виртуальный микрофон получит тишину

    # --- вывод в виртуальный микрофон (CABLE Input) ---
    def _cable_callback(self, outdata, frames, time_info, status):
        mic_part = self.mic_buffer.read(frames)
        tts_part = self.tts_cable_buffer.read(frames)
        mixed = np.clip(mic_part + tts_part, -1.0, 1.0)
        outdata[:, 0] = mixed

    # --- вывод в реальные динамики (только озвучка) ---
    def _speaker_callback(self, outdata, frames, time_info, status):
        tts_part = self.tts_speaker_buffer.read(frames)
        outdata[:, 0] = tts_part

    def start(self):
        self._mic_stream = sd.InputStream(
            device=self.mic_device, samplerate=SAMPLE_RATE, channels=1,
            blocksize=BLOCK_SIZE, callback=self._mic_callback,
        )
        self._cable_stream = sd.OutputStream(
            device=self.cable_device, samplerate=SAMPLE_RATE, channels=1,
            blocksize=BLOCK_SIZE, callback=self._cable_callback,
        )
        self._speaker_stream = sd.OutputStream(
            device=self.speaker_device, samplerate=SAMPLE_RATE, channels=1,
            blocksize=BLOCK_SIZE, callback=self._speaker_callback,
        )
        self._mic_stream.start()
        self._cable_stream.start()
        self._speaker_stream.start()

    def stop(self):
        for s in (self._mic_stream, self._cable_stream, self._speaker_stream):
            if s is not None:
                s.stop()
                s.close()

    def announce(self, text: str, gain: float = 1.0):
        """Синтезирует текст и отправляет его в виртуальный микрофон и в
        динамики. gain > 1.0 делает фразу громче обычной (например, для
        тревоги). Если за время синтеза речи (сетевой запрос к Google
        TTS) прилетел Ctrl+Q - озвучка не воспроизводится."""
        gen = self._current_generation()

        def _worker():
            pcm = text_to_pcm(text)
            if not self._is_current_generation(gen):
                return
            self.play_pcm(pcm, gain=gain)

        threading.Thread(target=_worker, daemon=True).start()

    def play_pcm(self, pcm: np.ndarray, gain: float = 1.0):
        """Отправляет уже готовый PCM-сигнал в виртуальный микрофон и в
        динамики. gain != 1.0 усиливает/ослабляет громкость (с обрезкой
        амплитуды, чтобы при усилении не было цифровых искажений)."""
        if gain != 1.0:
            pcm = np.clip(pcm * gain, -1.0, 1.0)
        self.tts_cable_buffer.write(pcm)
        self.tts_speaker_buffer.write(pcm)

    def announce_sound(self, sound_filename: str, text: str = None, gap_sec: float = 0.3, gain: float = 1.0):
        """Проигрывает звуковой файл из папки sounds/ (например, start.mp3,
        stop.mp3, alarm.mp3), и если задан text - следом озвучивает его
        через Google TTS. gain применяется и к звуку, и к фразе (для
        тревоги делаем оповещение громче обычного). Порядок гарантирован,
        т.к. всё пишется в буфер последовательно из одного фонового
        потока. Перед каждым шагом проверяет "поколение звука" - если за
        время декодирования mp3 или синтеза речи прилетел Ctrl+Q,
        оставшиеся шаги не воспроизводятся."""
        gen = self._current_generation()

        def _worker():
            sound_pcm = load_sound(sound_filename)
            if not self._is_current_generation(gen):
                return
            self.play_pcm(sound_pcm, gain=gain)

            if text:
                if not self._is_current_generation(gen):
                    return
                gap = np.zeros(int(gap_sec * SAMPLE_RATE), dtype=np.float32)
                self.play_pcm(gap)

                tts_pcm = text_to_pcm(text)
                if not self._is_current_generation(gen):
                    return
                self.play_pcm(tts_pcm, gain=gain)

        threading.Thread(target=_worker, daemon=True).start()


# ---------------------------------------------------------------------
# Расписание уроков и перемен
# ---------------------------------------------------------------------

def parse_end_times(times):
    return [datetime.datetime.strptime(t, "%H:%M").time() for t in times]


def build_day_schedule(end_times, duration_min, excluded_indices=None):
    """Строит список периодов на день: уроки (kind='lesson') и перемены
    между ними (kind='break'). Урок i длится duration_min минут и
    заканчивается в end_times[i]. Номера уроков начинаются с 0.
    Промежуток между концом урока и началом следующего (если он есть)
    становится периодом 'break'. excluded_indices - индексы уроков,
    которых в этот день недели нет вообще (например, {0} - без
    нулевого урока); перемены при этом считаются от реально
    оставшихся соседних уроков."""
    excluded_indices = excluded_indices or set()
    anchor_date = datetime.date(2000, 1, 1)  # опорная дата только для арифметики со временем
    duration = datetime.timedelta(minutes=duration_min)

    periods = []
    prev_end_dt = None
    for i, end_t in enumerate(end_times):
        if i in excluded_indices:
            continue

        end_dt = datetime.datetime.combine(anchor_date, end_t)
        start_dt = end_dt - duration

        if prev_end_dt is not None and start_dt > prev_end_dt:
            periods.append({
                "kind": "break",
                "index": i - 1,
                "start": prev_end_dt.time(),
                "end": start_dt.time(),
            })

        periods.append({
            "kind": "lesson",
            "index": i,
            "start": start_dt.time(),
            "end": end_t,
        })

        prev_end_dt = end_dt

    return periods


def build_weekly_schedule(end_times, duration_min, excluded_by_weekday):
    """Строит расписание на всю неделю: dict {день_недели: список периодов},
    где день_недели - 0=понедельник ... 6=воскресенье (как datetime.weekday()).
    excluded_by_weekday[день] может быть:
      - множеством/списком индексов уроков, которых в этот день нет;
      - строкой "ALL", если в этот день уроков вообще нет (выходной)."""
    schedule = {}
    for weekday in range(7):
        excluded = excluded_by_weekday.get(weekday, set())
        if excluded == "ALL":
            schedule[weekday] = []
        else:
            schedule[weekday] = build_day_schedule(end_times, duration_min, excluded_indices=set(excluded))
    return schedule


def get_current_period(now: datetime.datetime, weekly_schedule):
    """Возвращает (период, is_within) с учётом расписания по дням недели.
    is_within=True, если now попадает внутрь периода сегодняшнего дня.
    Если сегодня уроков уже/еще нет (в т.ч. если сегодня выходной) -
    ищет первый урок следующего дня, в котором уроки вообще есть
    (перебирая до 7 дней вперёд, чтобы пропустить выходные)."""
    today = now.date()
    today_periods = weekly_schedule.get(today.weekday(), [])

    candidates = []
    for p in today_periods:
        start_dt = datetime.datetime.combine(today, p["start"])
        end_dt = datetime.datetime.combine(today, p["end"])
        candidates.append({**p, "start_dt": start_dt, "end_dt": end_dt})

    for p in candidates:
        if p["start_dt"] <= now < p["end_dt"]:
            return p, True

    upcoming = [p for p in candidates if p["start_dt"] > now]
    if upcoming:
        return min(upcoming, key=lambda p: p["start_dt"]), False

    for delta in range(1, 8):
        day = today + datetime.timedelta(days=delta)
        periods = weekly_schedule.get(day.weekday(), [])
        if periods:
            first = periods[0]
            start_dt = datetime.datetime.combine(day, first["start"])
            end_dt = datetime.datetime.combine(day, first["end"])
            return {**first, "start_dt": start_dt, "end_dt": end_dt}, False

    return None, False


def scheduler_loop(router: AudioRouter, weekly_schedule, stop_event, state):
    prev_period_key = None
    announced_marks = set()   # (period_key, mark) - "N хвилин до кінця уроку X"
    first_tick = True

    while not stop_event.is_set():
        now = datetime.datetime.now()
        period, is_within = get_current_period(now, weekly_schedule)

        if period is None:
            # защитный случай: если в EXCLUDED_LESSONS_BY_WEEKDAY вообще
            # не осталось уроков ни на один день недели
            state["sleeping"] = True
            time.sleep(SLEEP_POLL_INTERVAL_SEC)
            continue

        period_key = (period["kind"], period["index"], period["start_dt"].isoformat())

        if is_within:
            seconds_until_start = 0.0
        else:
            seconds_until_start = (period["start_dt"] - now).total_seconds()

        # "Спим": уроки на сегодня закончились (или ещё не начались и до
        # первого больше ACTIVE_LEAD_SEC) - окно скрыто, ничего не считаем,
        # не озвучиваем и не дёргаем сеть (см. air_raid_loop).
        sleeping = (not is_within) and (seconds_until_start > ACTIVE_LEAD_SEC)
        state["sleeping"] = sleeping

        if sleeping:
            time.sleep(SLEEP_POLL_INTERVAL_SEC)
            continue

        state["period_end_str"] = period["end_dt"].strftime("%H:%M")

        if is_within:
            remaining_seconds = max(0, int((period["end_dt"] - now).total_seconds()))
            state["period_kind"] = period["kind"]
            state["lesson_index"] = period["index"]
            state["remaining_seconds"] = remaining_seconds

            is_new_period = period_key != prev_period_key

            if not first_tick and is_new_period and period["kind"] == "lesson":
                router.announce_sound("start.mp3", text=f"Урок номер {period['index']}")

            if period["kind"] == "lesson":
                for mark in ANNOUNCE_MARKS_MIN:
                    key = (period_key, mark)
                    if key not in announced_marks and remaining_seconds == mark * 60:
                        announced_marks.add(key)
                        word = ukrainian_plural(mark, "хвилина", "хвилини", "хвилин")
                        router.announce(f"До кінця уроку номер {period['index']}, {mark} {word}")

                end_key = (period_key, "end")
                if end_key not in announced_marks and remaining_seconds == 0:
                    announced_marks.add(end_key)
                    router.announce_sound("stop.mp3")

            # ключ "текущего активного периода" обновляем только здесь -
            # если делать это и в ветке "waiting" ниже, ключ ожидаемого
            # урока совпадёт с его же ключом в момент начала, и объявление
            # о начале урока перестанет срабатывать.
            prev_period_key = period_key
        else:
            remaining_seconds = max(0, int(seconds_until_start))
            state["period_kind"] = "waiting"
            state["lesson_index"] = period["index"] if period["kind"] == "lesson" else None
            state["remaining_seconds"] = remaining_seconds

        first_tick = False
        time.sleep(1)


def force_announce(router: AudioRouter, state):
    remaining = max(0, state.get("remaining_seconds", 0))
    kind = state.get("period_kind", "lesson")
    lesson_index = state.get("lesson_index")
    minutes, seconds = divmod(remaining, 60)

    if kind == "break":
        target = "кінця перерви"
    elif kind == "waiting":
        target = f"початку уроку номер {lesson_index}" if lesson_index is not None else "початку занять"
    else:
        target = f"кінця уроку номер {lesson_index}"

    min_word = ukrainian_plural(minutes, "хвилина", "хвилини", "хвилин")
    if minutes == 0:
        router.announce(f"До {target} залишилось менше хвилини")
    else:
        router.announce(f"{minutes} {min_word} до {target}")


def ptt_loop(router: AudioRouter, stop_event):
    while not stop_event.is_set():
        try:
            router.ptt_active = keyboard.is_pressed(PTT_KEY)
        except Exception:
            router.ptt_active = False
        time.sleep(0.01)


# ---------------------------------------------------------------------
# Ctrl+NumpadN - настраиваемые звуковые эффекты (разовые и циклические)
# из NUMPAD_SOUND_BINDINGS
# ---------------------------------------------------------------------

def loop_sound_worker(router: AudioRouter, filename: str, gain: float,
                       stop_event: threading.Event, active_event: threading.Event):
    """Пока active_event установлен (переключается соответствующим
    Ctrl+NumpadN) - циклично проигрывает filename из sounds/ без пауз
    между повторами. Проверяет флаг каждые 0.1с, чтобы выключение
    сработало практически сразу, а не только после того, как доиграет
    текущий повтор."""
    while not stop_event.is_set():
        if not active_event.is_set():
            time.sleep(0.1)
            continue

        pcm = load_sound(filename)
        if len(pcm) == 0:
            # файла нет / не удалось декодировать - не крутимся впустую
            time.sleep(1)
            continue

        router.play_pcm(pcm, gain=gain)

        duration = len(pcm) / SAMPLE_RATE
        waited = 0.0
        step = 0.1
        while waited < duration and active_event.is_set() and not stop_event.is_set():
            time.sleep(step)
            waited += step


def toggle_loop_sound(active_event: threading.Event):
    if active_event.is_set():
        active_event.clear()
    else:
        active_event.set()


def setup_numpad_sound_bindings(router: AudioRouter, stop_event: threading.Event) -> dict:
    """Запускает по одному фоновому потоку на каждую циклическую
    привязку из NUMPAD_SOUND_BINDINGS (loop=True). Возвращает
    {цифра: threading.Event} только для зацикленных привязок - этот
    словарь передаётся в register_ctrl_numpad_hotkeys (чтобы знать, что
    переключать) и в stop_everything (чтобы Ctrl+Q мог их все выключить)."""
    loop_events = {}
    for key, cfg in NUMPAD_SOUND_BINDINGS.items():
        if not cfg.get("loop", False):
            continue
        active = threading.Event()
        loop_events[key] = active
        threading.Thread(
            target=loop_sound_worker,
            args=(router, cfg["file"], cfg.get("gain", 1.0), stop_event, active),
            daemon=True,
        ).start()
    return loop_events


def stop_everything(router: AudioRouter, loop_events: dict):
    """Ctrl+Q: аварийная остановка вообще всех звуков. Останавливает
    все циклические привязки из NUMPAD_SOUND_BINDINGS и обрывает
    буферы + "поколение звука" в AudioRouter, из-за чего даже те
    озвучки (обычные фразы, sounds/start.mp3, тревога и т.п.), которые
    в данный момент ещё синтезируются/декодируются в фоне, не
    прозвучат, когда досчитаются."""
    for active in loop_events.values():
        active.clear()
    router.stop_all_sounds()


def register_ctrl_numpad_hotkeys(router: AudioRouter, loop_events: dict):
    """Ловит Ctrl+NumpadN для всех цифр из NUMPAD_SOUND_BINDINGS (не
    путает их с верхним рядом цифр - библиотека keyboard по умолчанию
    их не различает, см. комментарий у NUMPAD_SOUND_BINDINGS в
    настройках). Использует низкоуровневый keyboard.hook с проверкой
    event.is_keypad вместо keyboard.add_hotkey.

    Отдельно отслеживает "уже была нажата" для каждой привязанной
    клавиши и реагирует только на переход отпущена->нажата. Это важно:
    пока клавиша удерживается, ОС сама шлёт повторные события "down"
    (автоповтор), и без этой проверки переключатель мог бы сработать
    несколько раз за одно удержание и в итоге не остановиться при
    следующем нажатии."""
    ctrl_down = {"value": False}
    numpad_down = {key: False for key in NUMPAD_SOUND_BINDINGS}

    def _on_event(event):
        if event.name in ("ctrl", "left ctrl", "right ctrl"):
            ctrl_down["value"] = (event.event_type == "down")
            return

        if not getattr(event, "is_keypad", False):
            return
        if event.name not in numpad_down:
            return

        if event.event_type == "up":
            numpad_down[event.name] = False
            return

        if event.event_type != "down":
            return

        if numpad_down[event.name]:
            # автоповтор ОС при удержании клавиши - не считается новым нажатием
            return
        numpad_down[event.name] = True

        if not ctrl_down["value"]:
            return

        cfg = NUMPAD_SOUND_BINDINGS.get(event.name)
        if cfg is None:
            return

        if cfg.get("loop", False):
            active = loop_events.get(event.name)
            if active is not None:
                toggle_loop_sound(active)
        else:
            router.announce_sound(cfg["file"], gain=cfg.get("gain", 1.0))

    keyboard.hook(_on_event)


# ---------------------------------------------------------------------
# Воздушная тревога в Києві (alerts.in.ua)
# ---------------------------------------------------------------------

def _kyiv_air_raid_active() -> bool:
    """Запрашивает список активных тревог у alerts.in.ua и проверяет,
    есть ли среди них активная воздушная тревога конкретно по місту
    Києву (не по всій Київській області). ВНИМАНИЕ: имена полей
    ("alerts", "finished_at", "alert_type", "location_title")
    соответствуют документации alerts.in.ua на момент написания скрипта -
    если API изменится, проверьте актуальную схему на
    https://devs.alerts.in.ua и поправьте эту функцию."""
    req = urllib.request.Request(
        AIR_RAID_API_URL,
        headers={"Authorization": f"Bearer {AIR_RAID_API_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    for alert in payload.get("alerts", []):
        if alert.get("finished_at"):
            continue  # тревога уже завершена
        if alert.get("alert_type") != "air_raid":
            continue
        title = (alert.get("location_title") or "").strip()
        if title == AIR_RAID_CITY_TITLE:
            return True
    return False


def air_raid_loop(router: AudioRouter, stop_event, state):
    """Раз в AIR_RAID_POLL_INTERVAL_SEC секунд проверяет воздушную тревогу
    в Києві и озвучивает начало тревоги (переход "не було" -> "є", громко)
    и відбій (переход "було" -> "нема", обычной громкостью). Пока
    state["sleeping"] == True (уроки на сегодня закончились или ещё не
    начались) - запросы к серверу не отправляются вообще."""
    if not AIR_RAID_ENABLED:
        return
    if not AIR_RAID_API_TOKEN:
        print("[Тривога] AIR_RAID_API_TOKEN не задан - автооповещение о "
              "воздушной тревоге в Киеве отключено. Получите бесплатный "
              "токен на https://devs.alerts.in.ua и укажите его в "
              "AIR_RAID_API_TOKEN.")
        return

    was_active = False
    while not stop_event.is_set():
        if state.get("sleeping", False):
            # уроки не идут прямо сейчас и не начнутся в ближайшую минуту -
            # не дёргаем сервер и никого не оповещаем
            time.sleep(SLEEP_POLL_INTERVAL_SEC)
            continue

        try:
            is_active = _kyiv_air_raid_active()
        except Exception as e:
            print(f"[Тривога] Ошибка запроса к alerts.in.ua: {e}")
            time.sleep(AIR_RAID_POLL_INTERVAL_SEC)
            continue

        if is_active and not was_active:
            router.announce_sound(
                "alarm.mp3",
                text="Увага! В місті Києві оголошена повітряна тривога!",
                gain=AIR_RAID_VOLUME_GAIN,
            )
        elif was_active and not is_active:
            router.announce("Відбій повітряної тривоги")

        state["air_raid_active"] = is_active
        was_active = is_active
        time.sleep(AIR_RAID_POLL_INTERVAL_SEC)


# ---------------------------------------------------------------------
# Оверлей-таймер поверх всех окон
# ---------------------------------------------------------------------

class TimerOverlay:
    def __init__(self, state):
        self.state = state
        self.root = tk.Tk()
        self.root.overrideredirect(True)       # без рамки/заголовка
        self.root.attributes("-topmost", True)  # поверх всех окон
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("240x106+40+40")

        self.status_label = tk.Label(
            self.root, text="", font=("Consolas", 12, "bold"),
            fg="#cccccc", bg="#1e1e1e",
        )
        self.status_label.pack(fill="x", pady=(6, 0))

        self.time_label = tk.Label(
            self.root, text="--:--", font=("Consolas", 26, "bold"),
            fg=COLOR_LESSON, bg="#1e1e1e",
        )
        self.time_label.pack(expand=True, fill="both")

        self.end_label = tk.Label(
            self.root, text="", font=("Consolas", 11),
            fg="#999999", bg="#1e1e1e",
        )
        self.end_label.pack(fill="x", pady=(0, 6))

        self._drag_offset = (0, 0)
        for widget in (self.root, self.status_label, self.time_label, self.end_label):
            widget.bind("<Control-Button-1>", self._start_drag)
            widget.bind("<Control-B1-Motion>", self._do_drag)

        self._tick()

    def _start_drag(self, event):
        self._drag_offset = (
            event.x_root - self.root.winfo_x(),
            event.y_root - self.root.winfo_y(),
        )

    def _do_drag(self, event):
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def _tick(self):
        sleeping = self.state.get("sleeping", False)
        hidden_by_user = self.state.get("overlay_hidden_by_user", False)

        if sleeping or hidden_by_user:
            if self.root.state() != "withdrawn":
                self.root.withdraw()
            # пока скрыто - проверяем чаще, чем обычные 500мс, чтобы
            # Ctrl+Alt+E ощущался мгновенным, но реже, чем во время работы
            self.root.after(200, self._tick)
            return
        else:
            if self.root.state() == "withdrawn":
                self.root.deiconify()
                self.root.attributes("-topmost", True)  # на некоторых системах сбрасывается после withdraw

        remaining = self.state.get("remaining_seconds", 0)
        kind = self.state.get("period_kind", "lesson")
        lesson_index = self.state.get("lesson_index")
        end_str = self.state.get("period_end_str", "")

        m, s = divmod(max(0, remaining), 60)
        self.time_label.configure(text=f"{m:02d}:{s:02d}")
        self.end_label.configure(text=f"Кінець: {end_str}" if end_str else "")

        if kind == "break":
            self.time_label.configure(fg=COLOR_BREAK)
            self.status_label.configure(text="Перерва")
        elif kind == "waiting":
            self.time_label.configure(fg=COLOR_WAITING)
            if lesson_index is not None:
                self.status_label.configure(text=f"До уроку {lesson_index}")
            else:
                self.status_label.configure(text="Очікування")
        else:
            self.time_label.configure(fg=COLOR_LESSON)
            self.status_label.configure(text=f"Урок №{lesson_index}")

        self.root.after(500, self._tick)

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------
# Тот же таймер, но в виде отдельной виртуальной веб-камеры (для OBS /
# Zoom / Discord / Teams - выбирается там как обычная камера).
# ---------------------------------------------------------------------

_camera_font_time = None
_camera_font_status = None
_camera_font_alarm = None


def _get_camera_fonts():
    """Лениво загружает шрифты для рендера кадра камеры (чтобы PIL не
    импортировался, если виртуальная камера отключена)."""
    global _camera_font_time, _camera_font_status, _camera_font_alarm
    if _camera_font_time is not None:
        return _camera_font_time, _camera_font_status, _camera_font_alarm

    from PIL import ImageFont

    for family in ("consola.ttf", "DejaVuSansMono.ttf", "Arial.ttf"):
        try:
            _camera_font_time = ImageFont.truetype(family, 90)
            _camera_font_status = ImageFont.truetype(family, 26)
            break
        except Exception:
            continue

    # для надписи о тревоге пробуем взять жирный вариант шрифта, чтобы
    # она заметнее выделялась на кадре
    for family in ("consolab.ttf", "arialbd.ttf", "DejaVuSansMono-Bold.ttf", "consola.ttf"):
        try:
            _camera_font_alarm = ImageFont.truetype(family, 34)
            break
        except Exception:
            continue

    if _camera_font_time is None:
        _camera_font_time = ImageFont.load_default()
        _camera_font_status = ImageFont.load_default()
    if _camera_font_alarm is None:
        _camera_font_alarm = ImageFont.load_default()

    return _camera_font_time, _camera_font_status, _camera_font_alarm


def _render_timer_frame(state, width, height):
    """Рисует текущее состояние таймера как кадр (numpy RGB-массив) -
    тот же смысл, что и у TimerOverlay, только для виртуальной камеры.
    Если сейчас воздушная тревога (state["air_raid_active"]) - НАД
    таймером мигает красная надпись "Повітряна тривога!" с частотой
    1 раз в секунду (полсекунды видна, полсекунды скрыта)."""
    from PIL import Image, ImageDraw

    font_time, font_status, font_alarm = _get_camera_fonts()

    img = Image.new("RGB", (width, height), (30, 30, 30))
    draw = ImageDraw.Draw(img)

    if state.get("sleeping", False):
        text = "Немає уроків"
        bbox = draw.textbbox((0, 0), text, font=font_status)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, height // 2 - 15), text, fill=(120, 120, 120), font=font_status)
        return np.array(img)

    kind = state.get("period_kind", "lesson")
    lesson_index = state.get("lesson_index")
    remaining = state.get("remaining_seconds", 0)
    end_str = state.get("period_end_str", "")

    m, s = divmod(max(0, remaining), 60)
    time_text = f"{m:02d}:{s:02d}"

    if kind == "break":
        color = (255, 59, 59)
        status_text = "Перерва"
    elif kind == "waiting":
        color = (255, 204, 0)
        status_text = f"До уроку {lesson_index}" if lesson_index is not None else "Очікування"
    else:
        color = (0, 255, 136)
        status_text = f"Урок №{lesson_index}"

    draw.text((20, 16), status_text, fill=(200, 200, 200), font=font_status)

    bbox_time = draw.textbbox((0, 0), time_text, font=font_time)
    tw, th = bbox_time[2] - bbox_time[0], bbox_time[3] - bbox_time[1]
    draw.text(((width - tw) // 2, (height - th) // 2 - 10), time_text, fill=color, font=font_time)

    if end_str:
        end_text = f"Кінець: {end_str}"
        bbox_end = draw.textbbox((0, 0), end_text, font=font_status)
        tw_end = bbox_end[2] - bbox_end[0]
        draw.text(((width - tw_end) // 2, height - 44), end_text, fill=(150, 150, 150), font=font_status)

    if state.get("air_raid_active", False):
        # мигание раз в секунду: полсекунды видно, полсекунды скрыто
        blink_visible = int(time.time() * 2) % 2 == 0
        if blink_visible:
            alarm_text = "Повітряна тривога!"
            bbox_alarm = draw.textbbox((0, 0), alarm_text, font=font_alarm)
            tw_alarm = bbox_alarm[2] - bbox_alarm[0]
            draw.text(((width - tw_alarm) // 2, 54), alarm_text, fill=(255, 30, 30), font=font_alarm)

    return np.array(img)


def virtual_camera_loop(state, stop_event):
    """Непрерывно рисует кадр таймера и отправляет его в виртуальную
    камеру через pyvirtualcam. Если pyvirtualcam не установлен или
    камеру не удалось открыть (например, не установлен OBS Studio) -
    печатает предупреждение и просто не запускает камеру, остальной
    скрипт продолжает работать как обычно."""
    try:
        import pyvirtualcam
    except ImportError:
        print("[Камера] Библиотека pyvirtualcam не установлена - "
              "виртуальная камера-таймер отключена. Установите: "
              "pip install pyvirtualcam pillow (и OBS Studio - его "
              "виртуальная камера используется как драйвер).")
        return

    try:
        from PIL import Image  # noqa: F401 - проверяем, что Pillow установлен
    except ImportError:
        print("[Камера] Библиотека Pillow не установлена - виртуальная "
              "камера-таймер отключена. Установите: pip install pillow")
        return

    try:
        cam = pyvirtualcam.Camera(
            width=VIRTUAL_CAMERA_WIDTH, height=VIRTUAL_CAMERA_HEIGHT,
            fps=VIRTUAL_CAMERA_FPS, print_fps=False,
        )
    except Exception as e:
        print(f"[Камера] Не удалось открыть виртуальную камеру: {e}. "
              f"Убедитесь, что установлен OBS Studio (даже если сама "
              f"программа OBS не запущена - используется только его "
              f"драйвер) и что виртуальная камера не занята другим "
              f"приложением (в т.ч. самой OBS, если там нажата кнопка "
              f"'Start Virtual Camera').")
        return

    with cam:
        while not stop_event.is_set():
            frame_rgb = _render_timer_frame(state, VIRTUAL_CAMERA_WIDTH, VIRTUAL_CAMERA_HEIGHT)
            cam.send(frame_rgb)
            cam.sleep_until_next_frame()



# ---------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------

def toggle_overlay_visibility(state):
    """Переключатель для Ctrl+Alt+E: вручную показать/скрыть окно
    таймера на экране, независимо от автоматического режима "сна"."""
    state["overlay_hidden_by_user"] = not state.get("overlay_hidden_by_user", False)


def main():
    if "--list-devices" in sys.argv:
        list_devices()
        return

    mic_idx = find_device(REAL_MIC_NAME, "input")
    cable_idx = find_device(VIRTUAL_CABLE_NAME, "output")
    speaker_idx = find_device(SPEAKER_NAME, "output") if SPEAKER_NAME else None

    router = AudioRouter(mic_idx, cable_idx, speaker_idx)
    router.start()

    state = {
        "remaining_seconds": 0, "period_kind": "lesson", "lesson_index": None,
        "period_end_str": "", "sleeping": False, "air_raid_active": False,
        "overlay_hidden_by_user": False,
    }
    stop_event = threading.Event()
    end_times = parse_end_times(LESSON_END_TIMES)
    weekly_schedule = build_weekly_schedule(end_times, LESSON_DURATION_MIN, EXCLUDED_LESSONS_BY_WEEKDAY)

    threading.Thread(
        target=scheduler_loop, args=(router, weekly_schedule, stop_event, state), daemon=True
    ).start()
    threading.Thread(target=ptt_loop, args=(router, stop_event), daemon=True).start()
    threading.Thread(target=air_raid_loop, args=(router, stop_event, state), daemon=True).start()

    loop_events = setup_numpad_sound_bindings(router, stop_event)

    if ENABLE_VIRTUAL_CAMERA_TIMER:
        threading.Thread(target=virtual_camera_loop, args=(state, stop_event), daemon=True).start()

    keyboard.add_hotkey(HOTKEY_FORCE_ANNOUNCE, lambda: force_announce(router, state))
    keyboard.add_hotkey(HOTKEY_TOGGLE_OVERLAY, lambda: toggle_overlay_visibility(state))
    keyboard.add_hotkey(HOTKEY_STOP_ALL_SOUNDS, lambda: stop_everything(router, loop_events))
    register_ctrl_numpad_hotkeys(router, loop_events)

    try:
        if ENABLE_SCREEN_TIMER:
            overlay = TimerOverlay(state)
            overlay.run()
        else:
            # экранное окно отключено - просто держим процесс живым, чтобы
            # фоновые потоки (расписание, тревога, виртуальная камера)
            # продолжали работать; остановить - Ctrl+C в консоли.
            while not stop_event.is_set():
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        router.stop()


if __name__ == "__main__":
    main()