"""截图 + 模板匹配 + OCR 识别 + 元素查询。"""

import os, re, subprocess

import cv2

import macos

OCR_PATH = "/tmp/wechat_agent_1x.png"


def load_templates(names):
    """加载模板图片，返回 {name: ndarray}。"""
    templates = {}
    for name in names:
        path = f"resource/image/{name}.png"
        if os.path.exists(path):
            templates[name] = cv2.imread(path)
    return templates


def capture(wx, wy, ww, wh, scale, ocr_engine, templates):
    """截图 → 模板匹配 + OCR → 返回 (elements, img_w)。"""
    macos.activate_wechat()
    subprocess.run(
        ["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "-o", "/tmp/wechat_agent.png"],
        capture_output=True,
    )
    img = cv2.imread("/tmp/wechat_agent.png")
    img_w = img.shape[1]
    elements = []

    for name, tmpl in templates.items():
        result = cv2.matchTemplate(img, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.7:
            h, w = tmpl.shape[:2]
            elements.append({"type": "icon", "name": name,
                             "center": [max_loc[0] + w // 2, max_loc[1] + h // 2],
                             "size": [w, h]})

    small = cv2.resize(img, (img_w // scale, img.shape[0] // scale))
    cv2.imwrite(OCR_PATH, small)
    results, _ = ocr_engine(OCR_PATH)
    if results:
        for box, text, score in results:
            if not text.strip():
                continue
            cx = int((box[0][0] + box[2][0]) / 2) * scale
            cy = int((box[0][1] + box[2][1]) / 2) * scale
            panel = "left" if cx < img_w * 0.35 else "right"
            elements.append({"type": "text", "content": text.strip(),
                             "center": [cx, cy], "panel": panel})

    return elements, img_w


def find(elements, text):
    """按 name 或 content 查找元素。"""
    for e in elements:
        label = e.get("name") or e.get("content", "")
        if text in label:
            return e
    return None


def find_in_sidebar(elements, text, img_w):
    """在左侧栏查找联系人（跳过搜索框区域）。"""
    for e in elements:
        if e["type"] != "text":
            continue
        label = e.get("content", "")
        cx, cy = e["center"]
        if text in label and cx < img_w * 0.30 and cy > 100:
            return e
    return None


def get_chat_header(elements, img_w):
    """用搜索框位置作为锚点，定位右侧聊天标题。"""
    search_icon = find(elements, "搜索")

    candidates = []
    for e in elements:
        if e["type"] != "text":
            continue
        cx, cy = e["center"]
        content = e.get("content", "")
        if len(content) < 2 or re.match(r'^[\d:年月日昨今前天]+$', content):
            continue

        if search_icon:
            sx, sy = search_icon["center"]
            sw = search_icon.get("size", [240, 48])[0]
            if cx > sx + sw // 2 and abs(cy - sy) < 80:
                candidates.append(e)
        else:
            if cx > img_w * 0.30 and cy < 250:
                candidates.append(e)

    if candidates:
        candidates.sort(key=lambda e: e["center"][0])
        return candidates[0].get("content", "")
    return ""
