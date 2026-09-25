# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки виртуального аудио-кабеля
========================================================

Что делает
----------
1. Показывает список всех аудио-устройств (--list-devices).
2. Проигрывает тестовый сигнал (тональный гудок и/или фразу TTS) в
   ВХОД виртуального кабеля (например "CABLE Input") и ОДНОВРЕМЕННО
   записывает то, что приходит с ВЫХОДА этого же кабеля
   (например "CABLE Output").
3. Сохраняет запись в test_output.wav и печатает уровень сигнала
   (RMS/пик), чтобы сразу было видно: кабель реально передаёт звук
   или нет.
4. Дополнительно может проверить реальный микрофон (пишет с него
   несколько секунд и сохраняет отдельный wav) и реальные динамики
   (проигрывает гудок прямо на них, чтобы убедиться, что колонки
   слышны).

Использование
--------------
    python test_virtual_cable.py --list-devices

    python test_virtual_cable.py --cable-in "CABLE Input" --cable-out "CABLE Output"

    python test_virtual_cable.py --cable-in "CABLE Input" --cable-out "CABLE Output" \
        --mic "Microphone" --speaker "Speakers"

Если название устройства не задано явно, скрипт попробует угадать
"CABLE Input" / "CABLE Output" автоматически (стандартные имена
VB-Audio Virtual Cable).
"""

import sys
import time
import wave
import argparse
import threading

import numpy as np
import sounddevice as sd


SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
TEST_TONE_FREQ = 440.0     # Гц, нота "Ля"
TEST_TONE_DURATION = 3.0   # секунд


# ---------------------------------------------------------------------
# Поиск устройств
# ---------------------------------------------------------------------

def list_devices():
    print(sd.query_devices())


def find_device(name_substr, kind):
    """Ищет индекс устройства по подстроке имени. Возвращает None, если
    подстрока не задана, и бросает ошибку, если совпадений не найдено."""
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
        f"Устройство, содержащее '{name_substr}' ({kind}), не найдено. "
        f"Запустите со флагом --list-devices, чтобы увидеть точные названия."
    )


def guess_device(candidates, kind):
    """Пытается угадать устройство по списку типичных подстрок имени."""
    devices = sd.query_devices()
    for cand in candidates:
        for i, d in enumerate(devices):
            if cand.lower() in d["name"].lower():
                if kind == "input" and d["max_input_channels"] > 0:
                    return i
                if kind == "output" and d["max_output_channels"] > 0:
                    return i
    return None


# ---------------------------------------------------------------------
# Генерация тестового сигнала
# ---------------------------------------------------------------------

def make_test_tone(duration=TEST_TONE_DURATION, freq=TEST_TONE_FREQ, fade=0.05):
    n = int(duration * SAMPLE_RATE)
    t = np.linspace(0, duration, n, endpoint=False)
    tone = 0.4 * np.sin(2 * np.pi * freq * t).astype(np.float32)

    # лёгкое затухание на краях, чтобы не было щелчков
    fade_samples = int(fade * SAMPLE_RATE)
    if fade_samples > 0 and fade_samples * 2 < n:
        envelope = np.ones(n, dtype=np.float32)
        ramp = np.linspace(0, 1, fade_samples, dtype=np.float32)
        envelope[:fade_samples] = ramp
        envelope[-fade_samples:] = ramp[::-1]
        tone *= envelope

    return tone


def save_wav(path, data, samplerate=SAMPLE_RATE):
    pcm16 = np.clip(data, -1.0, 1.0)
    pcm16 = (pcm16 * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(pcm16.tobytes())


def rms(data):
    if len(data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(data))))


# ---------------------------------------------------------------------
# Тест 1: проигрываем гудок в CABLE Input, слушаем на CABLE Output
# ---------------------------------------------------------------------

def test_cable_loopback(cable_in_idx, cable_out_idx):
    print("\n=== Тест виртуального кабеля ===")
    print(f"Проигрываем тестовый тон {TEST_TONE_FREQ} Гц в устройство "
          f"вывода #{cable_in_idx} и одновременно слушаем на "
          f"устройстве записи #{cable_out_idx}...")

    tone = make_test_tone()
    recorded_chunks = []
    stop_event = threading.Event()

    def rec_callback(indata, frames, time_info, status):
        recorded_chunks.append(indata[:, 0].copy())

    rec_stream = sd.InputStream(
        device=cable_out_idx, samplerate=SAMPLE_RATE, channels=1,
        blocksize=BLOCK_SIZE, callback=rec_callback,
    )

    with rec_stream:
        # небольшая пауза перед началом, чтобы поток записи "прогрелся"
        time.sleep(0.2)
        sd.play(tone, samplerate=SAMPLE_RATE, device=cable_in_idx, blocking=True)
        # даём время дослушать хвост записи
        time.sleep(0.3)

    if recorded_chunks:
        recorded = np.concatenate(recorded_chunks)
    else:
        recorded = np.zeros(0, dtype=np.float32)

    level = rms(recorded)
    peak = float(np.max(np.abs(recorded))) if len(recorded) else 0.0

    save_wav("test_cable_output.wav", recorded)
    print(f"Записано {len(recorded)} сэмплов -> сохранено в test_cable_output.wav")
    print(f"RMS уровень: {level:.4f}   Пик: {peak:.4f}")

    if level > 0.01:
        print("РЕЗУЛЬТАТ: сигнал обнаружен — виртуальный кабель работает корректно.")
    else:
        print("РЕЗУЛЬТАТ: сигнал НЕ обнаружен. Проверьте:")
        print("  - правильно ли выбраны устройства (--cable-in / --cable-out);")
        print("  - что виртуальный кабель установлен и не отключен в системе;")
        print("  - что громкость устройства 'CABLE Input' не выставлена в 0.")


# ---------------------------------------------------------------------
# Тест 2: запись с реального микрофона (проверка, что микрофон жив)
# ---------------------------------------------------------------------

def test_real_mic(mic_idx, duration=3.0):
    print("\n=== Тест реального микрофона ===")
    print(f"Говорите что-нибудь в микрофон, идёт запись {duration} сек...")

    recorded_chunks = []

    def rec_callback(indata, frames, time_info, status):
        recorded_chunks.append(indata[:, 0].copy())

    with sd.InputStream(
        device=mic_idx, samplerate=SAMPLE_RATE, channels=1,
        blocksize=BLOCK_SIZE, callback=rec_callback,
    ):
        time.sleep(duration)

    recorded = np.concatenate(recorded_chunks) if recorded_chunks else np.zeros(0, dtype=np.float32)
    level = rms(recorded)
    peak = float(np.max(np.abs(recorded))) if len(recorded) else 0.0

    save_wav("test_mic_input.wav", recorded)
    print(f"Записано {len(recorded)} сэмплов -> сохранено в test_mic_input.wav")
    print(f"RMS уровень: {level:.4f}   Пик: {peak:.4f}")

    if level > 0.005:
        print("РЕЗУЛЬТАТ: микрофон улавливает звук.")
    else:
        print("РЕЗУЛЬТАТ: сигнал очень слабый или отсутствует — проверьте выбор "
              "устройства и его громкость/чувствительность в системе.")


# ---------------------------------------------------------------------
# Тест 3: проигрываем гудок прямо на реальные динамики
# ---------------------------------------------------------------------

def test_speaker(speaker_idx):
    print("\n=== Тест динамиков ===")
    print("Сейчас должен прозвучать тестовый тон из ваших динамиков...")
    tone = make_test_tone()
    sd.play(tone, samplerate=SAMPLE_RATE, device=speaker_idx, blocking=True)
    print("Если вы услышали гудок — динамики работают.")


# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Тест виртуального аудио-кабеля")
    parser.add_argument("--list-devices", action="store_true",
                         help="показать список всех аудио-устройств и выйти")
    parser.add_argument("--cable-in", default=None,
                         help="подстрока имени устройства ВХОДА кабеля (куда играем), напр. 'CABLE Input'")
    parser.add_argument("--cable-out", default=None,
                         help="подстрока имени устройства ЗАПИСИ с кабеля (что слышит приложение), напр. 'CABLE Output'")
    parser.add_argument("--mic", default=None,
                         help="подстрока имени реального микрофона (опционально, чтобы дополнительно проверить)")
    parser.add_argument("--speaker", default=None,
                         help="подстрока имени реальных динамиков (опционально, чтобы дополнительно проверить)")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    cable_in_idx = (find_device(args.cable_in, "output") if args.cable_in
                     else guess_device(["CABLE Input", "VB-Audio"], "output"))
    cable_out_idx = (find_device(args.cable_out, "input") if args.cable_out
                      else guess_device(["CABLE Output", "VB-Audio"], "input"))

    if cable_in_idx is None or cable_out_idx is None:
        print("Не удалось определить устройства виртуального кабеля автоматически.")
        print("Запустите с --list-devices и укажите их явно через --cable-in / --cable-out.")
        sys.exit(1)

    print(f"Устройство воспроизведения (вход кабеля): #{cable_in_idx} "
          f"({sd.query_devices(cable_in_idx)['name']})")
    print(f"Устройство записи (выход кабеля):         #{cable_out_idx} "
          f"({sd.query_devices(cable_out_idx)['name']})")

    test_cable_loopback(cable_in_idx, cable_out_idx)

    if args.mic:
        mic_idx = find_device(args.mic, "input")
        test_real_mic(mic_idx)

    if args.speaker:
        speaker_idx = find_device(args.speaker, "output")
        test_speaker(speaker_idx)

    print("\nГотово.")


if __name__ == "__main__":
    main()