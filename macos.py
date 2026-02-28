"""macOS 平台操作：窗口管理、鼠标点击、键盘输入。"""

import subprocess, time

from Quartz.CoreGraphics import (
    CGEventCreateMouseEvent, CGEventPost, CGPointMake,
    kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGMouseButtonLeft, kCGHIDEventTap,
)


def activate_wechat():
    subprocess.run(["osascript", "-e", 'tell application "WeChat" to activate'], capture_output=True)
    time.sleep(0.15)


def click(sx, sy):
    """CGEvent 鼠标点击（先激活微信）。"""
    activate_wechat()
    point = CGPointMake(sx, sy)
    event = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
    CGEventPost(kCGHIDEventTap, event)
    time.sleep(0.05)
    event = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
    CGEventPost(kCGHIDEventTap, event)


def type_text(text):
    """通过剪贴板粘贴文字。"""
    subprocess.run(["pbcopy"], input=text.encode(), capture_output=True)
    subprocess.run(["osascript", "-e", '''
tell application "System Events"
    tell process "WeChat"
        keystroke "v" using command down
    end tell
end tell'''], capture_output=True)


def press_key(keycode):
    subprocess.run(["osascript", "-e", f'''
tell application "System Events"
    tell process "WeChat"
        key code {keycode}
    end tell
end tell'''], capture_output=True)


def type_and_send(text):
    """粘贴文字并按回车发送（一次 osascript）。"""
    subprocess.run(["pbcopy"], input=text.encode(), capture_output=True)
    subprocess.run(["osascript", "-e", '''
tell application "System Events"
    tell process "WeChat"
        keystroke "v" using command down
        delay 0.2
        key code 36
    end tell
end tell'''], capture_output=True)


def get_wechat_bounds():
    """返回微信最大窗口的 (x, y, w, h)。"""
    script = '''
tell application "System Events"
    tell process "WeChat"
        set maxArea to 0
        set bestBounds to ""
        repeat with w in (every window)
            set pos to position of w
            set sz to size of w
            set a to (item 1 of sz) * (item 2 of sz)
            if a > maxArea then
                set maxArea to a
                set bestBounds to (item 1 of pos as text) & "," & (item 2 of pos as text) & "," & (item 1 of sz as text) & "," & (item 2 of sz as text)
            end if
        end repeat
        return bestBounds
    end tell
end tell'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return tuple(int(p) for p in r.stdout.strip().split(","))


def get_scale_factor():
    """返回屏幕缩放因子（Retina = 2）。"""
    r = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e",
         'ObjC.import("AppKit"); Math.round($.NSScreen.mainScreen.backingScaleFactor)'],
        capture_output=True, text=True,
    )
    return int(r.stdout.strip())
