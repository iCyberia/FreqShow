#!/usr/bin/env python3
import pygame
from PIL import Image
from evdev import InputDevice, ecodes, list_devices
import select
import time

import st7796_lcd as st7796
import controller
import model

DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320

# Touch mapping for your Goodix panel in landscape mode.
TOUCH_SWAP_XY = True
TOUCH_FLIP_X = True
TOUCH_FLIP_Y = False
TOUCH_DEBOUNCE_MS = 250


def get_cpu_temp() -> str:
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as f:
            temp_millic = int(f.read().strip())
        temp_c = temp_millic / 1000.0
        return f"{temp_c:.1f}C"
    except Exception:
        return "--.-C"


def surface_to_pil(surface: pygame.Surface) -> Image.Image:
    """Convert a pygame surface into a PIL Image for the LCD driver."""
    raw = pygame.image.tostring(surface, "RGB")
    width, height = surface.get_size()
    image = Image.frombytes("RGB", (width, height), raw)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    return image


def present_to_lcd(lcd, surface: pygame.Surface) -> None:
    """Push the pygame surface to the physical LCD."""
    lcd.show_image(surface_to_pil(surface))


def find_touch_device():
    """Find the touchscreen device."""
    try:
        return InputDevice("/dev/input/event0")
    except Exception:
        pass

    for path in list_devices():
        try:
            dev = InputDevice(path)
            name = (dev.name or "").lower()
            if "touch" in name or "goodix" in name or "xpt2046" in name or "ads7846" in name:
                return dev
        except Exception:
            pass
    return None


def get_touch_axes(dev):
    """Return axis codes and min/max values."""
    caps = dev.capabilities().get(ecodes.EV_ABS, [])
    abs_codes = {item[0] for item in caps}

    # Prefer normal single-touch axes first for this Goodix panel.
    if ecodes.ABS_X in abs_codes and ecodes.ABS_Y in abs_codes:
        x_code = ecodes.ABS_X
        y_code = ecodes.ABS_Y
    elif ecodes.ABS_MT_POSITION_X in abs_codes and ecodes.ABS_MT_POSITION_Y in abs_codes:
        x_code = ecodes.ABS_MT_POSITION_X
        y_code = ecodes.ABS_MT_POSITION_Y
    else:
        x_code = ecodes.ABS_X
        y_code = ecodes.ABS_Y

    try:
        x_info = dev.absinfo(x_code)
        y_info = dev.absinfo(y_code)
        x_min, x_max = x_info.min, x_info.max
        y_min, y_max = y_info.min, y_info.max
    except Exception:
        x_min, x_max = 0, 4095
        y_min, y_max = 0, 4095

    return x_code, y_code, x_min, x_max, y_min, y_max


def map_touch(raw_x, raw_y, width, height, x_min, x_max, y_min, y_max):
    """Map raw touch coordinates to screen coordinates."""
    if TOUCH_SWAP_XY:
        x = int((raw_y - y_min) * (width - 1) / max(1, (y_max - y_min)))
        y = int((raw_x - x_min) * (height - 1) / max(1, (x_max - x_min)))
    else:
        x = int((raw_x - x_min) * (width - 1) / max(1, (x_max - x_min)))
        y = int((raw_y - y_min) * (height - 1) / max(1, (y_max - y_min)))

    if TOUCH_FLIP_X:
        x = (width - 1) - x
    if TOUCH_FLIP_Y:
        y = (height - 1) - y

    return x, y


def poll_touch_click(dev, width, height, state, timeout=0.01):
    """Poll touchscreen and return one mapped click point on touch release."""
    if dev is None:
        return None

    x_code, y_code, x_min, x_max, y_min, y_max = get_touch_axes(dev)

    r, _, _ = select.select([dev.fd], [], [], timeout)
    if dev.fd not in r:
        return None

    click_point = None

    for event in dev.read():
        if event.type == ecodes.EV_ABS:
            if event.code == x_code:
                state["raw_x"] = event.value
            elif event.code == y_code:
                state["raw_y"] = event.value

        elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            if event.value == 1:
                state["down"] = True
            elif event.value == 0:
                if state["down"] and state["raw_x"] is not None and state["raw_y"] is not None:
                    click_point = map_touch(
                        state["raw_x"],
                        state["raw_y"],
                        width,
                        height,
                        x_min,
                        x_max,
                        y_min,
                        y_max,
                    )
                state["down"] = False

    return click_point


def draw_error_screen(screen: pygame.Surface, error_text: str) -> None:
    """Draw the startup/runtime error dialog."""
    screen.fill((20, 20, 20))

    width, height = screen.get_size()

    font_title = pygame.font.Font(None, 36)
    font_body = pygame.font.Font(None, 22)

    title = font_title.render("Startup Error", True, (255, 80, 80))
    title_rect = title.get_rect(center=(width // 2, height // 4))
    screen.blit(title, title_rect)

    lines = [
        "FreqShow hit an error during startup or runtime.",
        "",
        "Touch anywhere on the screen to try again.",
        "",
        f"Error: {error_text}",
    ]

    y = height // 4 + 40
    for line in lines:
        text = font_body.render(line, True, (230, 230, 230))
        text_rect = text.get_rect(center=(width // 2, y))
        screen.blit(text, text_rect)
        y += 28


def show_sdr_error(lcd, screen: pygame.Surface, error_text: str) -> bool:
    """Show the error screen until the user touches anywhere to retry."""
    touch_dev = find_touch_device()
    clock = pygame.time.Clock()
    touch_state = {"raw_x": None, "raw_y": None, "down": False}
    last_touch_ms = 0

    while True:
        draw_error_screen(screen, error_text)
        pygame.display.flip()
        present_to_lcd(lcd, screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_ESCAPE,
            ):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True

        point = poll_touch_click(
            touch_dev,
            screen.get_width(),
            screen.get_height(),
            touch_state,
            timeout=0.05,
        )
        if point is not None:
            now = pygame.time.get_ticks()
            if now - last_touch_ms >= TOUCH_DEBOUNCE_MS:
                last_touch_ms = now
                return True

        clock.tick(240)


def main() -> None:
    import traceback

    lcd = st7796.st7796()
    lcd.lcd_init()
    lcd.clear()

    pygame.init()
    screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    pygame.display.set_caption("FreqShow LCD")

    touch_dev = find_touch_device()

    while True:
        try:
            width, height = screen.get_size()

            fsmodel = model.FreqShowModel(width, height)
            fscontroller = controller.FreqShowController(fsmodel)

            clock = pygame.time.Clock()
            temp_font = pygame.font.Font(None, 22)
            last_temp_poll = 0.0
            cpu_temp_text = "--.-C"
            lcd_update_interval = 1.0 / 15.0
            last_lcd_update = 0.0
            running = True
            touch_state = {"raw_x": None, "raw_y": None, "down": False}
            last_touch_ms = 0
            last_fps_poll = 0.0
            fps_text = "-- FPS"


            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if hasattr(fscontroller.current(), "click"):
                            fscontroller.current().click(event.pos)

                point = poll_touch_click(
                    touch_dev,
                    screen.get_width(),
                    screen.get_height(),
                    touch_state,
                    timeout=0.01,
                )
                if point is not None:
                    now = pygame.time.get_ticks()
                    if now - last_touch_ms >= TOUCH_DEBOUNCE_MS:
                        last_touch_ms = now
                        print(f"APP CLICK {point}", flush=True)
                        if hasattr(fscontroller.current(), "click"):
                            fscontroller.current().click(point)

                now_time = time.time()
                if now_time - last_temp_poll >= 1.0:
                    cpu_temp_text = get_cpu_temp()
                    last_temp_poll = now_time

                if now_time - last_fps_poll >= 0.5:
                    fps_text = f"{clock.get_fps():.0f} FPS"
                    last_fps_poll = now_time

                fscontroller.current().render(screen)

                status_text = f"{fps_text}  {cpu_temp_text}"
                temp_surface = temp_font.render(status_text, True, (255, 255, 255))
                temp_rect = temp_surface.get_rect()
                temp_rect.bottomright = (screen.get_width() - 6, screen.get_height() - 6)
                screen.blit(temp_surface, temp_rect)

                pygame.display.flip()

                if now_time - last_lcd_update >= lcd_update_interval:
                    present_to_lcd(lcd, screen)
                    last_lcd_update = now_time

                clock.tick(240)

            try:
                fsmodel.cleanup()
            except Exception:
                pass

            break

        except Exception as e:
            print(f"FreqShow startup/runtime error: {e}", flush=True)
            with open("/home/hiroshi/FreqShow/freqshow_error.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {e}\n")
                traceback.print_exc(file=log_file)

            traceback.print_exc()
            retry = show_sdr_error(lcd, screen, str(e))
            if not retry:
                break

    pygame.quit()


if __name__ == "__main__":
    main()