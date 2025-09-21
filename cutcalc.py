"""
U字溝カットガイド - エラー回避版
Windows環境で確実に動作する最小構成版

カメラ機能、複雑なUI要素を一切使わない
最も基本的な機能のみ実装
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
import math
import os

# 日本語フォント設定
def setup_japanese_font():
    """日本語フォントを設定"""
    try:
        # Windowsの標準日本語フォントを登録
        if os.name == 'nt':  # Windows
            # メイリオフォントのパス
            meiryo_path = "C:/Windows/Fonts/meiryo.ttc"
            if os.path.exists(meiryo_path):
                LabelBase.register(name="Japanese", fn_regular=meiryo_path)
                return "Japanese"
            
            # MSゴシックフォントのパス
            msgothic_path = "C:/Windows/Fonts/msgothic.ttc"
            if os.path.exists(msgothic_path):
                LabelBase.register(name="Japanese", fn_regular=msgothic_path)
                return "Japanese"
                
        # その他のフォント（Linux/Mac用）
        system_fonts = [
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        ]
        
        for font_path in system_fonts:
            if os.path.exists(font_path):
                LabelBase.register(name="Japanese", fn_regular=font_path)
                return "Japanese"
                
    except Exception as e:
        print(f"フォント設定エラー: {e}")
    
    return None  # デフォルトフォントを使用

# フォント設定を実行
JAPANESE_FONT = setup_japanese_font()

class MinimalAngleGuide(BoxLayout):
    """最小限の角度ガイド"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 180
        
    def set_angle(self, angle):
        """角度を設定"""
        self.angle = angle
        self.draw_guide()
        
    def draw_guide(self):
        """ガイドを描画"""
        self.canvas.clear()
        
        if self.width == 0 or self.height == 0:
            Clock.schedule_once(lambda dt: self.draw_guide(), 0.1)
            return
            
        with self.canvas:
            # 背景
            Color(0.05, 0.05, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # ガイドライン
            Color(0.6, 1, 0.4, 1)
            
            center_x = self.width / 2
            center_y = self.height / 2
            radius = min(self.width, self.height) * 0.3
            
            # 中心点
            Ellipse(pos=(center_x - 4, center_y - 4), size=(8, 8))
            
            # 角度ライン
            start_angle = (180 - self.angle) / 2
            end_angle = start_angle + self.angle
            
            # 左ライン
            left_rad = math.radians(start_angle)
            left_x = center_x + radius * math.cos(left_rad)
            left_y = center_y + radius * math.sin(left_rad)
            Line(points=[center_x, center_y, left_x, left_y], width=2)
            
            # 右ライン
            right_rad = math.radians(end_angle)
            right_x = center_x + radius * math.cos(right_rad)
            right_y = center_y + radius * math.sin(right_rad)
            Line(points=[center_x, center_y, right_x, right_y], width=2)

class TestCutGuideApp(App):
    """テスト用アプリ"""
    
    def build(self):
        """UIを構築"""
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # タイトル（英語）
        title = Label(
            text="U-Channel Cut Guide - Test Version",
            size_hint_y=None,
            height=50,
            font_size=20,
            bold=True,
            font_name=JAPANESE_FONT
        )
        main_layout.add_widget(title)
        
        # 説明（英語）
        info = Label(
            text="Simple version for Windows environment",
            size_hint_y=None,
            height=30,
            font_size=14,
            color=(0.7, 0.7, 0.7, 1),
            font_name=JAPANESE_FONT
        )
        main_layout.add_widget(info)
        
        # 入力エリア
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        
        # 角度入力
        angle_box = BoxLayout(orientation='vertical')
        angle_box.add_widget(Label(
            text="Angle (deg)", 
            size_hint_y=None, 
            height=20,
            font_name=JAPANESE_FONT
        ))
        self.angle_input = TextInput(
            text="135",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        self.angle_input.bind(text=self.on_input_change)
        angle_box.add_widget(self.angle_input)
        input_layout.add_widget(angle_box)
        
        # 幅入力
        width_box = BoxLayout(orientation='vertical')
        width_box.add_widget(Label(
            text="Width (mm)", 
            size_hint_y=None, 
            height=20,
            font_name=JAPANESE_FONT
        ))
        self.width_input = TextInput(
            text="520",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        self.width_input.bind(text=self.on_input_change)
        width_box.add_widget(self.width_input)
        input_layout.add_widget(width_box)
        
        main_layout.add_widget(input_layout)
        
        # 計算ボタン
        calc_btn = Button(
            text="Calculate",
            size_hint_y=None,
            height=50,
            font_size=16,
            background_color=(0.2, 0.6, 0.2, 1),
            font_name=JAPANESE_FONT
        )
        calc_btn.bind(on_press=self.calculate)
        main_layout.add_widget(calc_btn)
        
        # 角度ガイド
        guide_label = Label(
            text="Angle Guide",
            size_hint_y=None,
            height=30,
            font_size=14,
            bold=True,
            font_name=JAPANESE_FONT
        )
        main_layout.add_widget(guide_label)
        
        # ガイド表示
        self.angle_guide = MinimalAngleGuide(size_hint_y=None, height=120)
        main_layout.add_widget(self.angle_guide)
        
        # スライダー
        slider_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        slider_layout.add_widget(Label(
            text="30", 
            size_hint_x=None, 
            width=30,
            font_name=JAPANESE_FONT
        ))
        
        self.slider = Slider(min=30, max=180, value=135, step=1)
        self.slider.bind(value=self.on_slider_change)
        slider_layout.add_widget(self.slider)
        
        slider_layout.add_widget(Label(
            text="180", 
            size_hint_x=None, 
            width=30,
            font_name=JAPANESE_FONT
        ))
        main_layout.add_widget(slider_layout)
        
        # 現在角度
        self.current_angle_label = Label(
            text="Current Angle: 135 deg",
            size_hint_y=None,
            height=25,
            font_size=12,
            font_name=JAPANESE_FONT
        )
        main_layout.add_widget(self.current_angle_label)
        
        # 結果表示
        result_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=10)
        
        # 切断角度
        angle_result = BoxLayout(orientation='vertical')
        angle_result.add_widget(Label(
            text="Cut Angle", 
            size_hint_y=None, 
            height=30,
            font_name=JAPANESE_FONT
        ))
        self.result_angle = Label(
            text="67.5 deg",
            size_hint_y=None,
            height=50,
            font_size=18,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=JAPANESE_FONT
        )
        angle_result.add_widget(self.result_angle)
        result_layout.add_widget(angle_result)
        
        # 切断長さ
        length_result = BoxLayout(orientation='vertical')
        length_result.add_widget(Label(
            text="Cut Length", 
            size_hint_y=None, 
            height=30,
            font_name=JAPANESE_FONT
        ))
        self.result_length = Label(
            text="216.5 mm",
            size_hint_y=None,
            height=50,
            font_size=18,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=JAPANESE_FONT
        )
        length_result.add_widget(self.result_length)
        result_layout.add_widget(length_result)
        
        main_layout.add_widget(result_layout)
        
        # ステータス
        self.status = Label(
            text="Ready",
            size_hint_y=None,
            height=40,
            color=(0.2, 0.7, 1, 1),
            font_name=JAPANESE_FONT
        )
        main_layout.add_widget(self.status)
        
        # 初期計算
        Clock.schedule_once(lambda dt: self.calculate_and_update(), 0.5)
        
        return main_layout
    
    def on_input_change(self, instance, value):
        """入力変更時"""
        try:
            angle = float(self.angle_input.text) if self.angle_input.text else 135
            angle = max(30, min(180, angle))
            self.slider.value = angle
            self.update_angle_guide(angle)
        except:
            pass
    
    def on_slider_change(self, instance, value):
        """スライダー変更時"""
        angle = int(value)
        self.angle_input.text = str(angle)
        self.current_angle_label.text = f"Current Angle: {angle} deg"
        self.update_angle_guide(angle)
        self.calculate_realtime()
    
    def update_angle_guide(self, angle):
        """角度ガイド更新"""
        self.angle_guide.set_angle(angle)
    
    def calculate_realtime(self):
        """リアルタイム計算"""
        try:
            angle = float(self.angle_input.text) if self.angle_input.text else 135
            width = float(self.width_input.text) if self.width_input.text else 520
            
            if angle >= 180:
                self.result_angle.text = "90.0 deg"
                self.result_length.text = "0.0 mm"
                return
            
            # 切断角度計算
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            
            # 切断長さ計算
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            
            self.result_angle.text = f"{cut_angle:.1f} deg"
            self.result_length.text = f"{cut_length:.1f} mm"
            
        except Exception as e:
            self.result_angle.text = "Error"
            self.result_length.text = "Error"
    
    def calculate(self, instance):
        """メイン計算"""
        try:
            self.status.text = "Calculating..."
            
            angle_text = self.angle_input.text
            width_text = self.width_input.text
            
            if not angle_text or not width_text:
                self.status.text = "Please enter angle and width"
                return
            
            angle = float(angle_text)
            width = float(width_text)
            
            if angle <= 0 or angle > 180:
                self.status.text = "Angle must be 1-180 degrees"
                return
            
            if width <= 0:
                self.status.text = "Width must be greater than 0"
                return
            
            # 計算実行
            if angle >= 180:
                self.result_angle.text = "90.0 deg"
                self.result_length.text = "0.0 mm"
                self.status.text = "Complete! (Straight line, no cut needed)"
                return
            
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            
            self.result_angle.text = f"{cut_angle:.1f} deg"
            self.result_length.text = f"{cut_length:.1f} mm"
            
            # スライダーとガイドも更新
            self.slider.value = angle
            self.update_angle_guide(angle)
            
            self.status.text = "Calculation complete!"
            
        except ValueError:
            self.status.text = "Please enter valid numbers"
        except Exception as e:
            self.status.text = f"Error: {str(e)}"
    
    def calculate_and_update(self):
        """初期計算と更新"""
        self.calculate_realtime()
        self.update_angle_guide(135)


# アプリ起動
if __name__ == '__main__':
    TestCutGuideApp().run()