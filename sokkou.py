# -*- coding: utf-8 -*-
# U字溝カットガイド（HTMLレイアウト寄せ・単一ファイル・VSCode/PC向け）
#
# 依存: pip install kivy
# PCでは Kivy 標準の Camera を利用（Androidは別途 camera4kivy を推奨だが本稿では未使用）
#
import math, os, datetime
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex, platform
from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp

# ---------------- フォント（日本語化） ----------------
def _register_jp_font():
    if platform == "win":
        for p in (r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\meiryo.ttc"):
            if os.path.exists(p):
                LabelBase.register(name="JP", fn_regular=p)
                return "JP"
    local = os.path.join(os.path.dirname(__file__), "NotoSansJP-Regular.otf")
    if os.path.exists(local):
        LabelBase.register(name="JP", fn_regular=local)
        return "JP"
    return None
JP_FONT = _register_jp_font()

# ---------------- ユーティリティ ----------------
def f2(x, default=0.0):
    try:
        return float(str(x).strip())
    except Exception:
        return float(default)

def clamp_angle_deg(d):
    try:
        d = float(d)
    except:
        return 90.0
    return max(1.0, min(179.0, d))

# ---------------- 見た目カード ----------------
class GlassCard(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(12)
        with self.canvas.before:
            Color(1, 1, 1, 0.12)
            self._bg = RoundedRectangle(radius=[dp(18)]*4)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

# 1行フォーム（ラベル縦＋入力縦を“2列横並び”するための箱）
class LabeledInput(BoxLayout):
    input = ObjectProperty(None)
    def __init__(self, title, default_text, unit_text="", **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.spacing = dp(6)
        # ラベル
        lab = Label(text=title, font_name=JP_FONT, font_size=sp(15),
                    color=(1,1,1,0.95), size_hint_y=None, height=dp(22),
                    halign="left", valign="middle")
        lab.bind(size=lambda *_: setattr(lab, "text_size", (lab.width, lab.height)))
        self.add_widget(lab)
        # 入力
        row = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(40))
        ti = TextInput(text=default_text, multiline=False, input_filter="float",
                       font_name=JP_FONT, font_size=sp(16),
                       foreground_color=(0,0,0,1),
                       background_normal="", background_active="",
                       background_color=(1,1,1,0.92),
                       cursor_color=(0,0,0,1))
        self.input = ti
        row.add_widget(ti)
        if unit_text:
            unit = Label(text=unit_text, font_name=JP_FONT, font_size=sp(15),
                         color=(1,1,1,0.95), size_hint=(None,1), width=dp(36),
                         halign="center", valign="middle")
            unit.bind(size=lambda *_: setattr(unit, "text_size", (unit.width, unit.height)))
            row.add_widget(unit)
        self.add_widget(row)

# 結果行
class ResultLine(Label):
    value = StringProperty("—")

# ---------------- メインアプリ ----------------
class CutApp(App):
    TITLE = "U字溝カットガイド"

    def build(self):
        # VSCodeで見やすいウィンドウサイズ
        if platform != "android":
            Window.size = (460, 860)

        root = FloatLayout()

        # 背景グラデ（上: #667eea / 下: #764ba2）
        with root.canvas.before:
            Color(*get_color_from_hex("#667EEA")); self._top = Rectangle()
            Color(*get_color_from_hex("#764BA2")); self._bot = Rectangle()
        def _bg(*_):
            w,h = root.size
            self._top.pos = root.pos; self._top.size = (w, h/2)
            self._bot.pos = (root.x, root.y+h/2); self._bot.size = (w, h/2)
        root.bind(size=_bg, pos=_bg)

        # スクロール全体
        scroll = ScrollView(size_hint=(1,1))
        root.add_widget(scroll)

        # メイン縦並び
        main = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14), size_hint_y=None)
        main.bind(minimum_height=lambda w,h: setattr(main, "height", h))
        scroll.add_widget(main)

        # 見出し
        header = BoxLayout(size_hint=(1,None), height=dp(50))
        title = Label(text=self.TITLE, font_name=JP_FONT, font_size=sp(20), bold=True,
                      color=(1,1,1,0.98), halign="left", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", (title.width, title.height)))
        header.add_widget(title)
        main.add_widget(header)

        # ===== 入力カード（HTMLの.input-section相当）=====
        in_card = GlassCard(size_hint=(1, None))
        main.add_widget(in_card)

        # 2列横並び（角度 / 幅）
        two_cols = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint=(1,None), height=dp(100))
        # 角度
        self.row_theta = LabeledInput("📐 曲げ角度", "135", "°", size_hint=(1,1))
        # 幅
        self.row_width = LabeledInput("📏 製品の幅", "300", "mm", size_hint=(1,1))
        two_cols.add_widget(self.row_theta)
        two_cols.add_widget(self.row_width)
        in_card.add_widget(two_cols)

        # ケーフ（任意：HTMLにはないけど実用で残す）
        self.row_kerf = LabeledInput("ケーフ(切断幅)", "2", "mm", size_hint=(1,None))
        self.row_kerf.height = dp(70)
        in_card.add_widget(self.row_kerf)

        # 大きい計算ボタン
        btn_calc = Button(text="🧮 計算する", size_hint=(1,None), height=dp(56),
                          font_name=JP_FONT, bold=True,
                          background_normal="", background_color=(0.27,0.72,0.38,1),
                          color=(1,1,1,1))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        in_card.add_widget(btn_calc)

        # ===== 結果カード（HTMLの.result相当）=====
        out_card = GlassCard(size_hint=(1, None))
        main.add_widget(out_card)

        # 結果見出し
        r_title = Label(text="📋 計算結果", font_name=JP_FONT, font_size=sp(18), bold=True,
                        color=(1,1,1,0.98), size_hint=(1,None), height=dp(28),
                        halign="center", valign="middle")
        r_title.bind(size=lambda *_: setattr(r_title, "text_size", (r_title.width, r_title.height)))
        out_card.add_widget(r_title)

        # 結果グリッド（2列）
        grid = GridLayout(cols=2, spacing=dp(8), size_hint=(1,None))
        grid.bind(minimum_height=lambda w,h: setattr(grid, "height", h))
        def add_res(lbl, attr):
            l = Label(text=lbl, font_name=JP_FONT, font_size=sp(15),
                      color=(1,1,1,0.95), size_hint_y=None, height=dp(26),
                      halign="left", valign="middle")
            l.bind(size=lambda *_: setattr(l, "text_size", (l.width, l.height)))
            v = ResultLine(text="—", font_name=JP_FONT, font_size=sp(16),
                           color=(1,1,1,0.98), size_hint_y=None, height=dp(26))
            setattr(self, attr, v)
            grid.add_widget(l); grid.add_widget(v)

        add_res("片側切断角 α (°)", "res_alpha")
        add_res("斜めカット線 長さ L (mm)", "res_L")
        add_res("tan(α)", "res_tan")
        add_res("伸び率 1/cos(α)", "res_sec")
        add_res("ケーフ補正 目安 K (mm)", "res_kerf")
        out_card.add_widget(grid)

        # ===== カメラカード（HTMLのcameraセクション風）=====
        cam_card = GlassCard(size_hint=(1, None))
        main.add_widget(cam_card)

        cam_title = Label(text="📷 カメラ角度ガイド", font_name=JP_FONT, font_size=sp(18), bold=True,
                          color=(1,1,1,0.98), size_hint=(1,None), height=dp(28),
                          halign="center", valign="middle")
        cam_title.bind(size=lambda *_: setattr(cam_title, "text_size", (cam_title.width, cam_title.height)))
        cam_card.add_widget(cam_title)

        # プレビュー枠
        self.cam_wrap = AnchorLayout(size_hint=(1,None), height=dp(210))
        self.cam_area = BoxLayout(size_hint=(1,1))  # Cameraをここに出し入れ
        self.cam_wrap.add_widget(self.cam_area)
        cam_card.add_widget(self.cam_wrap)

        # カメラ操作ボタン（横並び）
        cam_btns = BoxLayout(size_hint=(1,None), height=dp(48), spacing=dp(8))
        self.btn_cam_start = Button(text="📷 起動", font_name=JP_FONT,
                                    background_normal="", background_color=(1,1,1,0.18),
                                    color=(1,1,1,0.98))
        self.btn_cam_snap  = Button(text="📸 撮影", font_name=JP_FONT,
                                    background_normal="", background_color=(1,1,1,0.18),
                                    color=(1,1,1,0.98), disabled=True)
        self.btn_cam_stop  = Button(text="⏹ 停止", font_name=JP_FONT,
                                    background_normal="", background_color=(1,1,1,0.18),
                                    color=(1,1,1,0.98), disabled=True)
        cam_btns.add_widget(self.btn_cam_start)
        cam_btns.add_widget(self.btn_cam_snap)
        cam_btns.add_widget(self.btn_cam_stop)
        cam_card.add_widget(cam_btns)

        # ボタンの動作
        self.btn_cam_start.bind(on_release=lambda *_: self._camera_start())
        self.btn_cam_snap.bind(on_release=lambda *_: self._camera_snap())
        self.btn_cam_stop.bind(on_release=lambda *_: self._camera_stop())

        # 初期計算
        self.calculate()
        return root

    # --------- 軽いトースト ----------
    def toast(self, msg):
        from kivy.clock import Clock
        if hasattr(self, "_toast"):
            try: self.root.remove_widget(self._toast_box)
            except: pass
        lbl = Label(text=msg, font_name=JP_FONT, size_hint=(None,None),
                    size=(dp(320), dp(28)), color=(1,1,1,1),
                    halign="center", valign="middle")
        lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, lbl.height)))
        box = AnchorLayout(anchor_x="center", anchor_y="bottom", padding=dp(8), size_hint=(1,1))
        box.add_widget(lbl)
        self._toast_box = box; self._toast = lbl
        self.root.add_widget(box)
        Clock.schedule_once(lambda *_: self.root.remove_widget(box), 2.0)

    # --------- 計算 ----------
    def calculate(self):
        W = f2(self.row_width.input.text, 300.0)
        theta = clamp_angle_deg(f2(self.row_theta.input.text, 135.0))
        kerf = max(0.0, f2(self.row_kerf.input.text, 0.0))

        alpha = theta / 2.0
        rad = math.radians(alpha)
        cos_a = math.cos(rad) if abs(math.cos(rad)) > 1e-9 else 1e-9
        tan_a = math.tan(rad)
        sec_a = 1.0 / cos_a
        L = W * sec_a
        K = kerf * sec_a

        self.res_alpha.text = f"{alpha:.2f}"
        self.res_L.text = f"{L:.1f}"
        self.res_tan.text = f"{tan_a:.4f}"
        self.res_sec.text = f"{sec_a:.4f}"
        self.res_kerf.text = f"{K:.2f}"

    # --------- カメラ制御（PC/Kivy標準） ----------
    def _camera_start(self):
        # すでに起動していたら一旦停止
        self._camera_stop()

        try:
            cam = Camera(play=True, resolution=(1280, 720))
            cam.allow_stretch = True
            self._cam_widget = cam
            self.cam_area.clear_widgets()
            self.cam_area.add_widget(cam)

            self.btn_cam_start.disabled = True
            self.btn_cam_snap.disabled = False
            self.btn_cam_stop.disabled = True if platform=="macosx" else False  # macの仮想環境対策
            self.toast("カメラ起動")
        except Exception as e:
            self.toast(f"起動失敗: {e}")

    def _camera_snap(self):
        if not hasattr(self, "_cam_widget") or not self._cam_widget.texture:
            self.toast("カメラ未起動")
            return
        path = os.path.join(self.user_data_dir, f"shot_{datetime.datetime.now():%Y%m%d_%H%M%S}.png")
        try:
            self._cam_widget.texture.save(path)
            self.toast(f"保存: {path}")
        except Exception as e:
            self.toast(f"保存失敗: {e}")

    def _camera_stop(self):
        if hasattr(self, "_cam_widget"):
            try:
                self._cam_widget.play = False
            except: pass
            try:
                self.cam_area.remove_widget(self._cam_widget)
            except: pass
            delattr(self, "_cam_widget")
        self.btn_cam_start.disabled = False
        self.btn_cam_snap.disabled = True
        self.btn_cam_stop.disabled = True
        # プレビュー枠は空にして維持
        self.toast("停止")

if __name__ == "__main__":
    CutApp().run()
