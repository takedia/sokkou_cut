# -*- coding: utf-8 -*-
"""
U字溝カットガイド（カメラ版）- シンプル安定版
- 絵文字なし（文字化け対策）
- 左右バーを個別に調整できる2本スライダー
- ガイドは細く・長く・即時更新
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.logger import Logger
import math
import os
from glob import glob

# 画面サイズ（必要なら調整）
Window.size = (400, 700)

# 日本語フォント（あれば使う）
def setup_font():
    try:
        env_font = os.environ.get("KIVY_JP_FONT")
        if env_font and os.path.exists(env_font):
            LabelBase.register(name="Japanese", fn_regular=env_font)
            return "Japanese"

        candidates = []
        if os.name == 'nt':
            candidates = [
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/YuGothM.ttc",
                "C:/Windows/Fonts/msgothic.ttc",
            ]
        else:
            search_dirs = [
                "/usr/share/fonts", "/usr/local/share/fonts",
                os.path.expanduser("~/.local/share/fonts"),
                "/System/Library/Fonts", "/Library/Fonts",
            ]
            patterns = [
                "**/NotoSansJP*.otf", "**/NotoSansJP*.ttf",
                "**/NotoSansCJKjp*.otf", "**/SourceHanSansJP*.otf",
                "**/ipaexg.ttf", "**/ipagp.ttf", "**/ipam.ttf",
            ]
            for d in search_dirs:
                for p in patterns:
                    candidates.extend(glob(os.path.join(d, p), recursive=True))
        for path in candidates:
            if os.path.exists(path):
                LabelBase.register(name="Japanese", fn_regular=path)
                Logger.info(f"Font set: {path}")
                return "Japanese"
    except Exception as e:
        Logger.warning(f"Font setup failed: {e}")
    return None

FONT_NAME = setup_font()

# OpenCV（カメラは任意。動かなくてもアプリは落ちない）
try:
    import cv2
    OPENCV_AVAILABLE = True
except Exception:
    OPENCV_AVAILABLE = False
    Logger.warning("OpenCV unavailable. Camera buttons will still show but do nothing.")

class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.is_playing = False
        self.fps = 30

    def start(self, index=0):
        if not OPENCV_AVAILABLE:
            return False
        try:
            if self.capture:
                self.capture.release()
            self.capture = cv2.VideoCapture(index)
            if not self.capture.isOpened():
                return False
            self.is_playing = True
            Clock.schedule_interval(self._update, 1.0/self.fps)
            return True
        except Exception as e:
            Logger.error(f"Camera start error: {e}")
            return False

    def stop(self):
        self.is_playing = False
        Clock.unschedule(self._update)
        if self.capture:
            self.capture.release()
            self.capture = None
        self.texture = None

    def _update(self, dt):
        if not self.capture or not self.is_playing:
            return
        ok, frame = self.capture.read()
        if not ok:
            return
        frame = cv2.flip(frame, 0)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]
        tex = Texture.create(size=(w, h), colorfmt='rgb')
        tex.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        self.texture = tex

class AngleGuideOverlay(Widget):
    """薄く長い2本バー。左・右を度数で指定（0°=右、90°=上）。枠の内側で必ず止まる。"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.left_angle = 45.0
        self.right_angle = 135.0
        self.line_width = 2.0

        # ← 調整つまみ（質問の2点）
        self.length_ratio = 0.82   # 0.0〜1.0: 1.0で枠の端ピッタリ、0.9で10%短く
        self.center_bias  = -0.18   # -0.5〜+0.5くらい: +で上へ、-で下へ（高さに対する比）

        self.bind(size=self.update_overlay, pos=self.update_overlay)

    def set_angles(self, left_deg, right_deg):
        l = float(left_deg); r = float(right_deg)
        if r <= l:
            r = min(180.0, l + 1.0)
        self.left_angle, self.right_angle = l, r
        self.update_overlay()

    # ← インスタンスメソッドに変更（self を使えるように）
    def _edge_point(self, cx, cy, deg, x0, y0, x1, y1):
        rad = math.radians(deg)
        dx, dy = math.cos(rad), math.sin(rad)
        eps = 1e-9
        ts = []
        if dx > eps:      ts.append((x1 - cx) / dx)
        elif dx < -eps:   ts.append((x0 - cx) / dx)
        if dy > eps:      ts.append((y1 - cy) / dy)
        elif dy < -eps:   ts.append((y0 - cy) / dy)
        if not ts:
            return cx, cy
        t_edge = min([t for t in ts if t > 0], default=0.0)

        # 枠の端までの距離に ratio を掛けて短くする
        ratio = max(0.0, min(1.0, float(self.length_ratio)))
        t = ratio * t_edge
        return cx + dx * t, cy + dy * t

    def update_overlay(self, *args):
        self.canvas.after.clear()
        if self.width <= 0 or self.height <= 0:
            return

        # オーバーレイ自身の矩形（画像表示領域に合わせたい場合はここを差し替え）
        x0, y0 = self.x, self.y
        x1, y1 = self.x + self.width, self.y + self.height

        # 支点（中心）を上下にオフセット
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0 + self.center_bias * self.height

        # 交点（枠内）までで止める
        lx, ly = self._edge_point(cx, cy, self.left_angle,  x0, y0, x1, y1)
        rx, ry = self._edge_point(cx, cy, self.right_angle, x0, y0, x1, y1)

        with self.canvas.after:
            Color(0.65, 1.0, 0.35, 0.95)  # 左右バー
            Line(points=[cx, cy, lx, ly], width=self.line_width)
            Line(points=[cx, cy, rx, ry], width=self.line_width)
            Color(0.85, 1.0, 0.6, 0.95)   # 支点
            Ellipse(pos=(cx - 3, cy - 3), size=(6, 6))

class CameraGuideApp(App):
    def build(self):
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, scroll_type=['content'])
        root = BoxLayout(orientation='vertical', padding=10, spacing=8, size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))

        # タイトル
        title = Label(text="U字溝カットガイド", size_hint_y=None, height=30,
                      font_size=16, bold=True, font_name=FONT_NAME)
        subtitle = Label(text="カメラで角度を測って切断寸法を算出", size_hint_y=None, height=18,
                         font_size=10, color=(0.7,0.7,0.7,1), font_name=FONT_NAME)
        root.add_widget(title); root.add_widget(subtitle)

        # 入力
        inp = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=8)
        # 角度（手入力で計算したい時）
        left_box = BoxLayout(orientation='vertical')
        left_box.add_widget(Label(text="角度(°)", size_hint_y=None, height=15, font_size=10, font_name=FONT_NAME))
        self.angle_input = TextInput(text="135", input_filter='float', multiline=False,
                                     size_hint_y=None, height=40, font_size=12)
        left_box.add_widget(self.angle_input)
        inp.add_widget(left_box)

        # 幅
        width_box = BoxLayout(orientation='vertical')
        width_box.add_widget(Label(text="幅(mm)", size_hint_y=None, height=15, font_size=10, font_name=FONT_NAME))
        self.width_input = TextInput(text="520", input_filter='float', multiline=False,
                                     size_hint_y=None, height=40, font_size=12)
        width_box.add_widget(self.width_input)
        inp.add_widget(width_box)
        root.add_widget(inp)

        # 計算ボタン
        btn_calc = Button(text="計算実行", size_hint_y=None, height=42, font_size=14,
                          background_color=(0.2,0.7,0.2,1), font_name=FONT_NAME)
        btn_calc.bind(on_press=self.calculate_from_manual)
        root.add_widget(btn_calc)

        # カメラ＋ガイド
        cam_area = FloatLayout(size_hint_y=None, height=240)
        self.camera_view = CameraWidget(allow_stretch=True, keep_ratio=True,
                                        size_hint=(1,1), pos_hint={"x":0,"y":0})
        cam_area.add_widget(self.camera_view)

        self.overlay = AngleGuideOverlay(size_hint=(1,1), pos_hint={"x":0,"y":0})
        cam_area.add_widget(self.overlay)

        root.add_widget(cam_area)

        # 2本だけのスライダー
        sliders = BoxLayout(orientation='vertical', size_hint_y=None, height=90, spacing=4)
        self.info_label = Label(text="左: 45°  右: 135°  |  開き角: 90°  長さ: --- mm",
                                size_hint_y=None, height=18, font_size=11, font_name=FONT_NAME)
        sliders.add_widget(self.info_label)

        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=6)
        row1.add_widget(Label(text="左バー", size_hint_x=None, width=42, font_size=10, font_name=FONT_NAME))
        self.left_slider = Slider(min=0, max=180, value=45, step=1)
        row1.add_widget(self.left_slider)
        sliders.add_widget(row1)

        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=6)
        row2.add_widget(Label(text="右バー", size_hint_x=None, width=42, font_size=10, font_name=FONT_NAME))
        self.right_slider = Slider(min=0, max=180, value=135, step=1)
        row2.add_widget(self.right_slider)
        sliders.add_widget(row2)

        self.left_slider.bind(value=self.on_left_change)
        self.right_slider.bind(value=self.on_right_change)
        root.add_widget(sliders)

        # カメラ操作（絵文字なし）
        cam_btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=34, spacing=4)
        b1 = Button(text="カメラ起動", font_size=11, font_name=FONT_NAME)
        b2 = Button(text="撮影", font_size=11, font_name=FONT_NAME)
        b3 = Button(text="停止", font_size=11, font_name=FONT_NAME)
        b4 = Button(text="この角度で計算", font_size=11, font_name=FONT_NAME)

        b1.bind(on_press=self.start_camera)
        b3.bind(on_press=self.stop_camera)
        b4.bind(on_press=self.calculate_from_guide)

        cam_btns.add_widget(b1); cam_btns.add_widget(b2); cam_btns.add_widget(b3); cam_btns.add_widget(b4)
        root.add_widget(cam_btns)

        # ステータス & 結果
        self.status = Label(text="起動しました", size_hint_y=None, height=20, font_size=10,
                            color=(0.2,0.8,1,1), font_name=FONT_NAME)
        root.add_widget(self.status)

        res = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=8)
        left = BoxLayout(orientation='vertical')
        left.add_widget(Label(text="切断角度", size_hint_y=None, height=18, font_size=10, font_name=FONT_NAME))
        self.res_angle = Label(text="--.-°", font_size=16, bold=True, color=(0.2,0.8,0.2,1), font_name=FONT_NAME)
        left.add_widget(self.res_angle)
        res.add_widget(left)

        right = BoxLayout(orientation='vertical')
        right.add_widget(Label(text="切断長さ", size_hint_y=None, height=18, font_size=10, font_name=FONT_NAME))
        self.res_len = Label(text="--- mm", font_size=16, bold=True, color=(0.2,0.8,0.2,1), font_name=FONT_NAME)
        right.add_widget(self.res_len)
        res.add_widget(right)

        root.add_widget(res)

        # 初期計算表示
        self._update_overlay_and_info()

        scroll.add_widget(root)
        return scroll

    # -------- スライダー連動 --------
    def on_left_change(self, inst, val):
        v = int(val)
        # 右より小さく保つ
        if v >= self.right_slider.value:
            v = int(self.right_slider.value) - 1
            self.left_slider.value = max(0, v)
        self._update_overlay_and_info()

    def on_right_change(self, inst, val):
        v = int(val)
        if v <= self.left_slider.value:
            v = int(self.left_slider.value) + 1
            self.right_slider.value = min(180, v)
        self._update_overlay_and_info()

    def _update_overlay_and_info(self):
        l = int(self.left_slider.value)
        r = int(self.right_slider.value)
        self.overlay.set_angles(l, r)

        open_angle = r - l  # 0〜180の範囲に保っているのでそのまま差
        cut_len = self._calc_length(open_angle)

        self.info_label.text = f"左: {l}°  右: {r}°  |  開き角: {open_angle}°  長さ: {cut_len}"
        # 手入力欄は開き角を表示（分かりやすさ優先）
        self.angle_input.text = str(open_angle)

    # -------- 計算 --------
    def _calc_length(self, angle_deg):
        """開き角から切断長さを算出（幅はmm）"""
        try:
            width = float(self.width_input.text) if self.width_input.text else 520.0
        except:
            width = 520.0
        if angle_deg >= 180:
            return "0.0 mm"
        # 切断角 = 90 - (180 - 開き角)/2
        cut_angle = 90.0 - (180.0 - float(angle_deg)) / 2.0
        if cut_angle <= 0:
            return "--- mm"
        length = width / math.tan(math.radians(cut_angle))
        return f"{length:.1f} mm"

    def calculate_from_manual(self, *args):
        # angle_input は「開き角」を入れる前提
        try:
            a = float(self.angle_input.text)
        except:
            self.status.text = "角度を正しく入力してください"
            return
        self._apply_result_from_open_angle(a)

    def calculate_from_guide(self, *args):
        a = int(self.right_slider.value) - int(self.left_slider.value)
        self._apply_result_from_open_angle(a)

    def _apply_result_from_open_angle(self, open_angle):
        if not (1 <= open_angle <= 180):
            self.status.text = "角度は1〜180°の範囲で"
            return
        cut_angle = 90.0 - (180.0 - float(open_angle)) / 2.0
        if cut_angle <= 0:
            self.status.text = "角度が小さすぎます"
            return
        try:
            width = float(self.width_input.text)
        except:
            self.status.text = "幅(mm)を入力してください"
            return
        length = width / math.tan(math.radians(cut_angle))
        self.res_angle.text = f"{cut_angle:.1f}°"
        self.res_len.text = f"{length:.1f} mm"
        self.status.text = "計算完了"

    # -------- カメラ --------
    def start_camera(self, *args):
        if self.camera_view.start(0):
            self.status.text = "カメラ起動"
        else:
            self.status.text = "カメラを起動できませんでした"

    def stop_camera(self, *args):
        self.camera_view.stop()
        self.status.text = "カメラ停止"

if __name__ == "__main__":
    CameraGuideApp().run()
