#!/usr/bin/env python3
"""WeChat automation agent: 打开聊天 + 发送消息。"""

import sys, time, warnings
from contextlib import contextmanager

warnings.filterwarnings("ignore")

from rapidocr_onnxruntime import RapidOCR

import macos
import vision


# ─── 计时工具 ─────────────────────────────────────────────────────────────────

@contextmanager
def step(desc):
    t0 = time.time()
    yield
    print(f"[{time.time() - t0:.2f}s] {desc}")


# ─── WeChatAgent ──────────────────────────────────────────────────────────────

class WeChatAgent:

    def __init__(self):
        self.ocr_engine = RapidOCR()
        self.templates = vision.load_templates(["搜索", "toolbar"])
        self.wx = self.wy = self.ww = self.wh = 0
        self.scale = 2
        self.elements = []
        self.img_w = 0

    def connect(self):
        """激活微信，获取窗口边界和缩放因子。"""
        macos.activate_wechat()
        self.wx, self.wy, self.ww, self.wh = macos.get_wechat_bounds()
        self.scale = macos.get_scale_factor()
        print(f"  窗口: ({self.wx},{self.wy}) {self.ww}x{self.wh} @{self.scale}x")

    def _to_screen(self, ix, iy):
        """图像像素坐标 → 屏幕坐标。"""
        return self.wx + ix // self.scale, self.wy + iy // self.scale

    def _capture(self):
        """截图 + OCR，更新 self.elements / self.img_w。"""
        self.elements, self.img_w = vision.capture(
            self.wx, self.wy, self.ww, self.wh,
            self.scale, self.ocr_engine, self.templates,
        )

    # ── 业务流程 ──────────────────────────────────────────────────────────

    def open_chat(self, contact):
        """确保目标聊天窗口已打开。成功返回 True。"""
        with step("截图 + OCR"):
            self._capture()
        print(f"  ({len(self.elements)} 个元素)")

        header = vision.get_chat_header(self.elements, self.img_w)
        print(f"[检测] 当前聊天: {header!r}")

        if contact in header:
            print(f"  已在「{contact}」聊天窗口")
            return True

        sidebar_match = vision.find_in_sidebar(self.elements, contact, self.img_w)
        if sidebar_match:
            cx, cy = sidebar_match["center"]
            sx, sy = self._to_screen(cx, cy)
            print(f"  点击侧栏「{contact}」 img=({cx},{cy}) screen=({sx},{sy})")
            with step("点击侧栏"):
                macos.click(sx, sy)
                time.sleep(0.5)
            return True

        return self._search_contact(contact)

    def _search_contact(self, contact):
        """通过搜索框查找并打开联系人。"""
        print(f"  侧栏未找到「{contact}」，执行搜索...")

        search_icon = vision.find(self.elements, "搜索")
        if search_icon:
            cx, cy = search_icon["center"]
            sx, sy = self._to_screen(cx, cy)
            print(f"  点击搜索 img=({cx},{cy}) screen=({sx},{sy})")
        else:
            sx = self.wx + self.ww * 18 // 100
            sy = self.wy + self.wh * 4 // 100
            print(f"  点击搜索（估算位置） screen=({sx},{sy})")
        with step("点击搜索"):
            macos.click(sx, sy)
            time.sleep(0.5)

        with step(f"输入 {contact!r}"):
            macos.type_text(contact)
            time.sleep(1.0)

        with step("搜索结果 OCR"):
            self._capture()
        result = vision.find_in_sidebar(self.elements, contact, self.img_w) \
            or vision.find(self.elements, contact)
        if not result:
            print(f"  搜索未找到「{contact}」")
            return False

        cx, cy = result["center"]
        sx, sy = self._to_screen(cx, cy)
        print(f"  点击搜索结果「{contact}」 img=({cx},{cy}) screen=({sx},{sy})")
        with step("点击结果"):
            macos.click(sx, sy)
            time.sleep(0.5)

        with step("Esc 关闭搜索"):
            macos.press_key(53)
            time.sleep(0.3)

        return True

    def send(self, message):
        """点击输入框 → 输入消息 → 发送。"""
        input_x = self.wx + (self.ww * 65 // 100)
        input_y = self.wy + (self.wh * 92 // 100)
        with step(f"点击输入框 ({input_x},{input_y})"):
            macos.click(input_x, input_y)
            time.sleep(0.2)

        with step(f"输入 + 发送 {message!r}"):
            macos.type_and_send(message)


# ─── 入口 ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-contact", required=True)
    parser.add_argument("-message", required=True)
    args = parser.parse_args()

    print(f"目标: 给「{args.contact}」发消息「{args.message}」")

    with step("初始化 OCR + 模板"):
        agent = WeChatAgent()
    with step("连接微信"):
        agent.connect()

    t_start = time.time()
    if not agent.open_chat(args.contact):
        return 1
    agent.send(args.message)

    print(f"\n已发送！总耗时 {time.time() - t_start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
