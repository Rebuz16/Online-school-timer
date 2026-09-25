# -*- coding: utf-8 -*-
"""
Тест всех оповещений и таймеров lesson_mic_timer.py
======================================================

Проверяет по очереди:
  1. Оповещение о начале урока: sounds/start.mp3 + "Урок номер N".
  2. Оповещение о конце урока: sounds/stop.mp3 (без номера).
  3. Начало воздушной тревоги: sounds/alarm.mp3 + фраза - ГРОМЧЕ всех
     остальных оповещений (AIR_RAID_VOLUME_GAIN), сразу следом играет
     фраза обычной громкости для сравнения на слух.
  4. Отбой воздушной тревоги: "Відбій повітряної тривоги" (обычная громкость).
  5. Правильность склонений числительных для минут и секунд.
  6. Расписание по дням недели (EXCLUDED_LESSONS_BY_WEEKDAY) - без звука,
     просто печатает, какие уроки есть в каждый день, и прогоняет
     контрольные точки "сна"/пробуждения на реальном дне с уроками.
  7. Рендер кадра виртуальной камеры для нескольких состояний -
     сохраняет PNG-превью, чтобы посмотреть, как это будет выглядеть
     в Zoom/OBS, даже без физической виртуальной камеры.
  8. Разовый эффект sounds/grasshoppers.mp3 (как по Ctrl+Numpad2).
  9. Тихий циклический sounds/wait.mp3 (как по Ctrl+Numpad1) - несколько
     секунд проигрывания по кругу, затем автоматическая остановка -
     чтобы на слух проверить и громкость (WAIT_LOOP_VOLUME_GAIN), и то,
     что повторы идут без пауз/щелчков между собой.
  10. Аварийная остановка (как по Ctrl+Q) - запускает длинную фразу и
      обрывает её через секунду; звук должен резко прекратиться, а не
      доиграть до конца.

Файл должен лежать в той же папке, что и lesson_mic_timer.py (он
импортирует из него готовые функции и классы, чтобы не дублировать
логику и не разойтись с основным скриптом).

Установка/запуск - как у основного скрипта:
    pip install sounddevice numpy keyboard gTTS
    (плюс ffmpeg в PATH; для теста камеры - pillow)

Примеры запуска:
    python test_sounds.py --list-devices
    python test_sounds.py --speaker "Speakers"
    python test_sounds.py --only sleep
    python test_sounds.py --only camera
    python test_sounds.py --only alarm
    python test_sounds.py --only grasshoppers
    python test_sounds.py --only wait_loop
    python test_sounds.py --only stop_all
"""

import time
import datetime
import argparse
import threading

import lesson_mic_timer as lmt


def wait_and_report(label: str, seconds: float):
    print(f"   -> {label}")
    time.sleep(seconds)


def test_lesson_start(router):
    print("\n=== Тест 1: начало урока (start.mp3 + номер) ===")
    router.announce_sound("start.mp3", text="Урок номер 0")
    wait_and_report("start.mp3 + 'Урок номер 0'", 4)


def test_lesson_stop(router):
    print("\n=== Тест 2: конец урока (stop.mp3, без номера) ===")
    router.announce_sound("stop.mp3")
    wait_and_report("stop.mp3", 3)


def test_air_raid_start(router):
    print("\n=== Тест 3: НАЧАЛО тревоги - должно звучать громче обычного ===")
    print(f"   (используется AIR_RAID_VOLUME_GAIN = {lmt.AIR_RAID_VOLUME_GAIN})")
    router.announce_sound(
        "alarm.mp3",
        text="Увага! В місті Києві оголошена повітряна тривога!",
        gain=lmt.AIR_RAID_VOLUME_GAIN,
    )
    wait_and_report("alarm.mp3 + фраза про тривогу (громко)", 6)

    router.announce("Це фраза звичайної голосності для порівняння")
    wait_and_report("обычная фраза (для сравнения громкости на слух)", 4)


def test_air_raid_end(router):
    print("\n=== Тест 4: ВІДБІЙ тревоги - обычная громкость ===")
    router.announce("Відбій повітряної тривоги")
    wait_and_report("'Відбій повітряної тривоги'", 3)


def test_grasshoppers(router):
    print("\n=== Тест 8: разовый эффект grasshoppers.mp3 (Ctrl+Numpad2) ===")
    router.announce_sound("grasshoppers.mp3")
    wait_and_report("grasshoppers.mp3", 4)


def test_wait_loop(router):
    """Имитирует Ctrl+Numpad1: несколько секунд крутит sounds/wait.mp3
    по кругу тихо, затем сама останавливает - чтобы проверить и цикл,
    и громкость, без необходимости реально жать хоткей."""
    print("\n=== Тест 9: циклический wait.mp3 (Ctrl+Numpad1), тихо ===")
    print(f"   (используется WAIT_LOOP_VOLUME_GAIN = {lmt.WAIT_LOOP_VOLUME_GAIN})")

    active = threading.Event()
    active.set()
    t = threading.Thread(target=lmt.wait_sound_loop, args=(router, threading.Event(), active), daemon=True)
    t.start()
    wait_and_report("wait.mp3 крутится по кругу...", 7)

    active.clear()
    print("   -> остановлено (имитация повторного Ctrl+Numpad1)")
    time.sleep(0.5)


def test_stop_all(router):
    """Имитирует Ctrl+Q: запускает длинную фразу и через секунду
    обрывает её router.stop_all_sounds() - звук должен резко
    прекратиться, а не доиграть до конца."""
    print("\n=== Тест 10: аварийная остановка (Ctrl+Q) ===")
    text = ("Це дуже довга фраза для перевірки аварійної зупинки, "
             "вона має обірватися на середині, а не дограти до кінця")
    print(f"   -> запускаю длинную фразу: '{text[:40]}...'")
    router.announce(text)
    wait_and_report("играет ~1 секунду...", 1)
    print("   -> вызываю stop_all_sounds() (имитация Ctrl+Q)")
    router.stop_all_sounds()
    print("   Если звук резко прервался - тест пройден.")
    print("   Если фраза доиграла до конца - проверьте, что используете")
    print("   актуальную версию lesson_mic_timer.py с методом stop_all_sounds().")
    time.sleep(1)


def test_minute_declension(router):
    print("\n=== Тест 5: склонение минут ('хвилина/хвилини/хвилин') ===")
    for minutes in (1, 2, 5, 11, 15, 21):
        word = lmt.ukrainian_plural(minutes, "хвилина", "хвилини", "хвилин")
        text = f"До кінця уроку номер 0, {minutes} {word}"
        router.announce(text)
        wait_and_report(text, 3)


def test_second_declension(router):
    print("\n=== Тест 6: склонение секунд ('секунда/секунди/секунд') ===")
    for seconds in (1, 2, 5, 11, 21):
        word = lmt.ukrainian_plural(seconds, "секунда", "секунди", "секунд")
        text = f"{seconds} {word} до кінця перерви"
        router.announce(text)
        wait_and_report(text, 3)


def test_weekly_schedule():
    """Без звука: печатает, какие уроки есть в каждый день недели по
    вашему EXCLUDED_LESSONS_BY_WEEKDAY, и прогоняет контрольные точки
    "сна"/пробуждения на ближайшем дне, где уроки действительно есть."""
    print("\n=== Тест 7: расписание по дням недели ===")
    end_times = lmt.parse_end_times(lmt.LESSON_END_TIMES)
    weekly = lmt.build_weekly_schedule(end_times, lmt.LESSON_DURATION_MIN, lmt.EXCLUDED_LESSONS_BY_WEEKDAY)

    names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Субота", "Воскресенье"]
    for wd in range(7):
        lessons = [p["index"] for p in weekly[wd] if p["kind"] == "lesson"]
        print(f"   {names[wd]:12s}: уроки {lessons if lessons else '(выходной)'}")

    # ближайший день недели, где уроки есть - на нём проверяем сон/пробуждение
    today = datetime.date.today()
    day_with_lessons = None
    for delta in range(7):
        d = today + datetime.timedelta(days=delta)
        if weekly[d.weekday()]:
            day_with_lessons = d
            break

    if day_with_lessons is None:
        print("   Ни в один день недели уроков нет - пропускаю проверку сна/пробуждения.")
        return

    periods = weekly[day_with_lessons.weekday()]
    first_start = periods[0]["start"]
    last_end = periods[-1]["end"]
    print(f"\n   Контрольные точки на {names[day_with_lessons.weekday()]} "
          f"({first_start} - {last_end}), ACTIVE_LEAD_SEC = {lmt.ACTIVE_LEAD_SEC} сек:")

    def combine(t):
        return datetime.datetime.combine(day_with_lessons, t)

    checkpoints = [
        ("за 2 минуты до первого урока", (combine(first_start) - datetime.timedelta(minutes=2)).time()),
        ("за 30 секунд до первого урока", (combine(first_start) - datetime.timedelta(seconds=30)).time()),
        ("в момент начала первого урока", first_start),
        ("сразу после конца последнего урока", (combine(last_end) + datetime.timedelta(minutes=1)).time()),
    ]

    for label, t in checkpoints:
        now = combine(t)
        period, is_within = lmt.get_current_period(now, weekly)
        seconds_until_start = 0.0 if is_within else (period["start_dt"] - now).total_seconds()
        sleeping = (not is_within) and (seconds_until_start > lmt.ACTIVE_LEAD_SEC)
        print(f"   {label:38s} ({t.strftime('%H:%M:%S')}): "
              f"sleeping={sleeping!s:5s}  период={period['kind']} #{period['index']}  is_within={is_within}")


def test_camera_frames():
    """Рендерит несколько тестовых состояний таймера кадрами виртуальной
    камеры и сохраняет их как PNG - чтобы посмотреть, как это будет
    выглядеть в Zoom/OBS, не открывая физическую виртуальную камеру."""
    print("\n=== Тест 8: рендер кадра виртуальной камеры (PNG-превью) ===")
    try:
        from PIL import Image
    except ImportError:
        print("   Pillow не установлен (pip install pillow) - тест пропущен.")
        return

    samples = {
        "lesson": {"period_kind": "lesson", "lesson_index": 3, "remaining_seconds": 754,
                   "period_end_str": "13:55", "sleeping": False},
        "break": {"period_kind": "break", "lesson_index": 2, "remaining_seconds": 300,
                  "period_end_str": "12:25", "sleeping": False},
        "waiting": {"period_kind": "waiting", "lesson_index": 0, "remaining_seconds": 45,
                    "period_end_str": "11:35", "sleeping": False},
        "sleeping": {"sleeping": True},
        "air_raid": {"period_kind": "lesson", "lesson_index": 3, "remaining_seconds": 754,
                     "period_end_str": "13:55", "sleeping": False, "air_raid_active": True},
    }
    for name, state in samples.items():
        frame = lmt._render_timer_frame(state, lmt.VIRTUAL_CAMERA_WIDTH, lmt.VIRTUAL_CAMERA_HEIGHT)
        path = f"camera_preview_{name}.png"
        Image.fromarray(frame).save(path)
        print(f"   -> сохранено {path} ({frame.shape[1]}x{frame.shape[0]})")
    print("   (air_raid сохранён в текущий момент времени - надпись может")
    print("    попасть как в 'видимую', так и в 'скрытую' фазу мигания)")


def main():
    parser = argparse.ArgumentParser(description="Тест оповещений и таймеров lesson_mic_timer")
    parser.add_argument("--list-devices", action="store_true",
                         help="показать список аудио-устройств и выйти")
    parser.add_argument("--cable-in", default=lmt.VIRTUAL_CABLE_NAME,
                         help="устройство вывода в виртуальный кабель (по умолчанию - из lesson_mic_timer.py)")
    parser.add_argument("--speaker", default=lmt.SPEAKER_NAME,
                         help="устройство вывода на динамики (по умолчанию - из lesson_mic_timer.py)")
    parser.add_argument("--only",
                         choices=["start", "stop", "alarm", "alarm_end", "minutes", "seconds",
                                  "sleep", "camera", "grasshoppers", "wait_loop", "stop_all"],
                         help="прогнать только один конкретный тест вместо всех")
    args = parser.parse_args()

    if args.list_devices:
        lmt.list_devices()
        return

    # Эти два теста звука/аудио-устройств не требуют
    if args.only == "sleep":
        test_weekly_schedule()
        return
    if args.only == "camera":
        test_camera_frames()
        return

    cable_idx = lmt.find_device(args.cable_in, "output") if args.cable_in else None
    speaker_idx = lmt.find_device(args.speaker, "output") if args.speaker else None

    # Реальный микрофон для этого теста не нужен - используем устройство
    # записи по умолчанию, чтобы AudioRouter мог нормально запуститься.
    mic_idx = None

    print(f"Устройство виртуального кабеля: "
          f"{'по умолчанию' if cable_idx is None else lmt.sd.query_devices(cable_idx)['name']}")
    print(f"Устройство динамиков:           "
          f"{'по умолчанию' if speaker_idx is None else lmt.sd.query_devices(speaker_idx)['name']}")
    print(f"Папка со звуками:               {lmt.SOUNDS_DIR}\n")

    router = lmt.AudioRouter(mic_idx, cable_idx, speaker_idx)
    router.start()

    tests = {
        "start": test_lesson_start,
        "stop": test_lesson_stop,
        "alarm": test_air_raid_start,
        "alarm_end": test_air_raid_end,
        "minutes": test_minute_declension,
        "seconds": test_second_declension,
        "grasshoppers": test_grasshoppers,
        "wait_loop": test_wait_loop,
        "stop_all": test_stop_all,
    }

    try:
        if args.only:
            tests[args.only](router)
        else:
            for fn in tests.values():
                fn(router)
    finally:
        router.stop()

    if not args.only:
        test_weekly_schedule()
        test_camera_frames()

    print("\nГотово.")
    print("Если какой-то из звуков (start/stop/alarm) не прозвучал -")
    print(f"проверьте, что соответствующий .mp3 лежит в {lmt.SOUNDS_DIR}")
    print("Если не прозвучала озвучка текста - проверьте интернет и ffmpeg в PATH.")
    print("Тревога (тест 3) должна звучать заметно громче обычной фразы после неё -")
    print("если разница не слышна, увеличьте AIR_RAID_VOLUME_GAIN в lesson_mic_timer.py.")
    print("Ctrl+Alt+E (в самом lesson_mic_timer.py, не в этом тесте) вручную")
    print("показывает/скрывает окно таймера на экране.")


if __name__ == "__main__":
    main()