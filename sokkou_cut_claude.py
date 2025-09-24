import math
import os

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


def _register_japanese_capable_font():
    """Register a font that can render Japanese glyphs when possible."""

    candidates = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(current_dir, "fonts")

    if os.path.isdir(fonts_dir):
        for filename in sorted(os.listdir(fonts_dir)):
            lower = filename.lower()
            if lower.endswith((".ttf", ".otf", ".ttc")):
                candidates.append(os.path.join(fonts_dir, filename))

    candidates.extend(
        [
            "/system/fonts/NotoSansCJK-Regular.ttc",
            "/system/fonts/NotoSansJP-Regular.otf",
            "/system/fonts/NotoSansCJKjp-Regular.otf",
            "/system/fonts/DroidSansFallback.ttf",
            "/system/fonts/MTLmr3m.ttf",
            "/system/fonts/MSGothic.ttc",
            "/system/fonts/Meiryo.ttc",
            os.path.expanduser("~/Library/Fonts/NotoSansCJKjp-Regular.otf"),
            os.path.expanduser("~/Library/Fonts/NotoSansJP-Regular.otf"),
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
        ]
    )

    for path in candidates:
        if not path or not os.path.exists(path):
            continue

        try:
            LabelBase.register(
                name="Roboto",
                fn_regular=path,
                fn_bold=path,
                fn_italic=path,
                fn_bolditalic=path,
            )
            return path
        except Exception:
            continue

    return ""


REGISTERED_FONT_PATH = _register_japanese_capable_font()

KV = '''
<SokkouCutClaudeWidget>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(12)
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(16)
            canvas.before:
                Color:
                    rgba: 0.14, 0.1, 0.22, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(16),]

            Label:
                text: "U字溝カットガイド"
                font_size: dp(28)
                size_hint_y: None
                height: self.texture_size[1] + dp(20)
                bold: True
                halign: "center"
                text_size: self.width, None

            Label:
                text: "Python / Kivy 版"
                font_size: dp(18)
                color: 0.8, 0.8, 0.95, 1
                size_hint_y: None
                height: self.texture_size[1] + dp(10)
                halign: "center"
                text_size: self.width, None

            BoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                canvas.before:
                    Color:
                        rgba: 0.12, 0.1, 0.18, 0.9
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(12),]

                Label:
                    text: "計算パラメータ"
                    font_size: dp(20)
                    size_hint_y: None
                    height: self.texture_size[1] + dp(8)
                    halign: "left"
                    text_size: self.width, None

                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    Label:
                        text: "折れ後の内角 φ (度)"
                        font_size: dp(16)
                        size_hint_y: None
                        height: dp(40)
                        halign: "left"
                        valign: "middle"
                        text_size: self.size

                    TextInput:
                        id: angle_input
                        text: root.target_angle_text
                        multiline: False
                        write_tab: False
                        input_filter: "float"
                        halign: "center"
                        font_size: dp(18)
                        size_hint_y: None
                        height: dp(40)
                        on_text: root.on_target_angle_change(self.text)

                    Label:
                        text: "製品幅 W (mm)"
                        font_size: dp(16)
                        size_hint_y: None
                        height: dp(40)
                        halign: "left"
                        valign: "middle"
                        text_size: self.size

                    TextInput:
                        id: width_input
                        text: root.width_text
                        multiline: False
                        write_tab: False
                        input_filter: "float"
                        halign: "center"
                        font_size: dp(18)
                        size_hint_y: None
                        height: dp(40)
                        on_text: root.on_width_change(self.text)

                Button:
                    text: "計算する"
                    font_size: dp(18)
                    size_hint_y: None
                    height: dp(44)
                    on_press: root.calculate()

                Button:
                    text: "初期値にリセット"
                    font_size: dp(16)
                    size_hint_y: None
                    height: dp(40)
                    on_press: root.reset_values()

                Label:
                    text: root.status_message
                    color: root.status_color
                    font_size: dp(16)
                    size_hint_y: None
                    height: self.texture_size[1] + dp(6)
                    halign: "center"
                    text_size: self.width, None

            BoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
                canvas.before:
                    Color:
                        rgba: 0.1, 0.08, 0.16, 0.9
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(12),]

                Label:
                    text: "計算結果"
                    font_size: dp(22)
                    size_hint_y: None
                    height: self.texture_size[1] + dp(6)
                    halign: "left"
                    text_size: self.width, None

                GridLayout:
                    cols: 1
                    spacing: dp(6)
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: dp(40)

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "切断角度"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.cut_angle_result
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "切断長さ"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.cut_length_result
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "Δ = 180° − φ"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.delta_result
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "Δ/2 (留め角)"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.miter_result
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "水平基準角"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.angle_from_horizontal
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "垂直基準角"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.angle_from_vertical
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "控え寸法 s"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.s_result
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size

                    BoxLayout:
                        spacing: dp(6)
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "端部オフセット x"
                            font_size: dp(18)
                            size_hint_x: 0.5
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.x_result
                            font_size: dp(20)
                            size_hint_x: 0.5
                            halign: "center"
                            valign: "middle"
                            text_size: self.size
'''

class SokkouCutClaudeWidget(BoxLayout):
    target_angle_text = StringProperty("180")
    width_text = StringProperty("520")

    status_message = StringProperty("角度と幅を入力して計算ボタンを押してください")
    status_color = ListProperty([0.8, 0.8, 0.9, 1])

    cut_angle_result = StringProperty("---°")
    cut_length_result = StringProperty("--- mm")
    delta_result = StringProperty("---°")
    miter_result = StringProperty("---°")
    angle_from_horizontal = StringProperty("---°")
    angle_from_vertical = StringProperty("---°")
    s_result = StringProperty("--- mm")
    x_result = StringProperty("--- mm")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        base_message = "角度と幅を入力して計算ボタンを押してください"

        if REGISTERED_FONT_PATH:
            font_name = os.path.basename(REGISTERED_FONT_PATH)
            self.status_message = (
                f"{base_message}\n(日本語フォント {font_name} を使用しています)"
            )
            self.status_color = [0.7, 0.85, 1.0, 1]
        else:
            self.status_message = (
                base_message
                + "\n日本語フォントが見つかりません。端末に日本語対応フォントを追加してください"
            )
            self.status_color = [0.95, 0.75, 0.5, 1]

    def on_target_angle_change(self, text):
        self.target_angle_text = text.strip()

    def on_width_change(self, text):
        self.width_text = text.strip()

    def reset_values(self):
        self.target_angle_text = "180"
        self.width_text = "520"
        if "angle_input" in self.ids:
            self.ids.angle_input.text = self.target_angle_text
        if "width_input" in self.ids:
            self.ids.width_input.text = self.width_text
        self.status_message = "初期値にリセットしました"
        self.status_color = [0.7, 0.9, 0.7, 1]
        self.clear_results()

    def clear_results(self):
        self.cut_angle_result = "---°"
        self.cut_length_result = "--- mm"
        self.delta_result = "---°"
        self.miter_result = "---°"
        self.angle_from_horizontal = "---°"
        self.angle_from_vertical = "---°"
        self.s_result = "--- mm"
        self.x_result = "--- mm"

    def calculate(self):
        try:
            angle = float(self.target_angle_text)
            width = float(self.width_text)
        except ValueError:
            self.status_message = "数値を入力してください"
            self.status_color = [0.95, 0.5, 0.5, 1]
            self.clear_results()
            return

        if not (0 < angle <= 180):
            self.status_message = "角度は1°〜180°の範囲で入力してください"
            self.status_color = [0.95, 0.5, 0.5, 1]
            self.clear_results()
            return

        if width <= 0:
            self.status_message = "製品幅は0より大きい値を入力してください"
            self.status_color = [0.95, 0.5, 0.5, 1]
            self.clear_results()
            return

        half_angle = (180 - angle) / 2.0
        cut_angle = 90.0 - half_angle

        if angle >= 180:
            self.cut_angle_result = "90.0°"
            self.cut_length_result = "0.0 mm"
            self.delta_result = "0.0°"
            self.miter_result = "0.0°"
            self.angle_from_horizontal = "90.0°"
            self.angle_from_vertical = "0.0°"
            self.s_result = "0.0 mm"
            self.x_result = "0.0 mm"
            self.status_message = "180°は直線のため切断長さ0"
            self.status_color = [0.6, 0.9, 0.6, 1]
            return

        cut_angle_rad = math.radians(cut_angle)
        tan_value = math.tan(cut_angle_rad)

        if abs(tan_value) < 1e-9:
            self.status_message = "計算中にエラーが発生しました (tanが0)"
            self.status_color = [0.95, 0.5, 0.5, 1]
            self.clear_results()
            return

        cut_length = width / tan_value
        delta = 180.0 - angle
        miter = delta / 2.0
        angle_from_horizontal = 90.0 - miter
        angle_from_vertical = miter
        miter_rad = math.radians(miter)
        s_value = width * math.tan(miter_rad)
        x_value = (width / 2.0) * math.tan(miter_rad)

        self.cut_angle_result = f"{cut_angle:.1f}°"
        self.cut_length_result = f"{cut_length:.1f} mm"
        self.delta_result = f"{delta:.1f}°"
        self.miter_result = f"{miter:.1f}°"
        self.angle_from_horizontal = f"{angle_from_horizontal:.1f}°"
        self.angle_from_vertical = f"{angle_from_vertical:.1f}°"
        self.s_result = f"{s_value:.1f} mm"
        self.x_result = f"{x_value:.1f} mm"

        self.status_message = "計算完了！"
        self.status_color = [0.6, 0.9, 0.6, 1]

class SokkouCutClaudeApp(App):
    def build(self):
        Builder.load_string(KV)
        return SokkouCutClaudeWidget()

if __name__ == "__main__":
    SokkouCutClaudeApp().run()
