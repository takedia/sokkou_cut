from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
import math

KV = '''
<CutCalcWidget>:
    orientation: "vertical"
    padding: 20
    spacing: 10

    Label:
        text: "U字溝カットガイド"
        font_size: 24
        size_hint_y: None
        height: 40

    BoxLayout:
        spacing: 10
        size_hint_y: None
        height: 40
        Label:
            text: "角度"
        TextInput:
            id: angle_input
            text: "180"
            input_filter: "float"
            multiline: False
        Label:
            text: "°"
        Label:
            text: "幅"
        TextInput:
            id: width_input
            text: "520"
            input_filter: "float"
            multiline: False
        Label:
            text: "mm"

    Button:
        text: "計算する"
        size_hint_y: None
        height: 40
        on_press: root.calculate()

    Label:
        id: status
        text: ""
        color: 1,0,0,1
        size_hint_y: None
        height: 30

    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: 80
        Label:
            text: "切断角度: " + root.result_angle
            font_size: 18
        Label:
            text: "切断長さ: " + root.result_length
            font_size: 18
'''

class CutCalcWidget(BoxLayout):
    result_angle = StringProperty("---")
    result_length = StringProperty("---")

    def calculate(self):
        try:
            angle = float(self.ids.angle_input.text)
            width = float(self.ids.width_input.text)
            if not (1 <= angle <= 180):
                self.ids.status.text = "角度は1°〜180°で入力してください"
                return
            if width <= 0:
                self.ids.status.text = "幅は0より大きい値を入力してください"
                return
            if angle >= 180:
                cut_angle = 90.0
                cut_length = 0.0
                self.result_angle = f"{cut_angle:.1f}°"
                self.result_length = f"{cut_length:.1f} mm"
                self.ids.status.text = "180°は直線のため切断長さ0"
                return
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            self.result_angle = f"{cut_angle:.1f}°"
            self.result_length = f"{cut_length:.1f} mm"
            self.ids.status.text = "計算完了！"
        except Exception as e:
            self.ids.status.text = f"入力エラー: {e}"

class CutCalcApp(App):
    def build(self):
        Builder.load_string(KV)
        return CutCalcWidget()

if __name__ == "__main__":
    CutCalcApp().run()
