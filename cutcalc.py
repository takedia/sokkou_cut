# -*- coding: utf-8 -*-
"""
U字溝カットガイド - 構文エラー修正版
確実に動作する完全版

修正内容:
- 構文エラーを完全に修正
- try-except文の適切な構造
- インデントの統一
- 文字列リテラルの修正
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
import math
import os

# ウィンドウサイズ設定（デバッグ用）
Window.size = (380, 650)

# フォント設定
def setup_font():
    """日本語フォント設定"""
    try:
        if os.name == 'nt':  # Windows
            font_paths = [
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/msgothic.ttc"
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    LabelBase.register(name="Japanese", fn_regular=font_path)
                    return "Japanese"
    except Exception as e:
        print(f"フォント設定エラー: {e}")
    return None

FONT_NAME = setup_font()

# OpenCV確認
try:
    import cv2
    OPENCV_AVAILABLE = True
    print("OpenCV利用可能")
except ImportError:
    OPENCV_AVAILABLE = False
    print("OpenCV利用不可 - カメラ機能は無効")

class SimpleAngleGuide(BoxLayout):
    """シンプル角度ガイド描画ウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 135
        self.bind(size=self.update_guide)
        
    def set_angle(self, angle):
        """角度設定"""
        self.angle = angle
        self.update_guide()
        
    def update_guide(self, *args):
        """ガイド描画更新"""
        self.canvas.clear()
        
        if self.width == 0 or self.height == 0:
            Clock.schedule_once(lambda dt: self.update_guide(), 0.1)
            return
            
        try:
            with self.canvas:
                # 背景色
                Color(0.05, 0.05, 0.15, 1)
                Rectangle(pos=self.pos, size=self.size)
                
                # ガイドライン色
                Color(0.4, 0.9, 0.4, 1)
                
                center_x = self.width / 2
                center_y = self.height / 2
                radius = min(self.width, self.height) * 0.35
                
                # 中心点
                Ellipse(pos=(center_x - 4, center_y - 4), size=(8, 8))
                
                # 角度計算
                start_angle = (180 - self.angle) / 2
                end_angle = start_angle + self.angle
                
                # 左側ライン
                left_rad = math.radians(start_angle)
                left_x = center_x + radius * math.cos(left_rad)
                left_y = center_y + radius * math.sin(left_rad)
                Line(points=[center_x, center_y, left_x, left_y], width=3)
                
                # 右側ライン
                right_rad = math.radians(end_angle)
                right_x = center_x + radius * math.cos(right_rad)
                right_y = center_y + radius * math.sin(right_rad)
                Line(points=[center_x, center_y, right_x, right_y], width=3)
                
        except Exception as e:
            print(f"ガイド描画エラー: {e}")

class ScrollCutGuideApp(App):
    """メインアプリケーションクラス"""
    
    def build(self):
        """UIを構築"""
        # メインスクロールビュー
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            scroll_type=['content'],
            bar_width=8
        )
        
        # メインレイアウト
        main_layout = BoxLayout(
            orientation='vertical',
            padding=15,
            spacing=10,
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # ヘッダー追加
        header = self.create_header()
        main_layout.add_widget(header)
        
        # 入力セクション追加
        input_section = self.create_input_section()
        main_layout.add_widget(input_section)
        
        # 計算ボタン追加
        calc_btn = Button(
            text="🧮 計算実行",
            size_hint_y=None,
            height=50,
            font_size=16,
            background_color=(0.2, 0.7, 0.2, 1),
            font_name=FONT_NAME
        )
        calc_btn.bind(on_press=self.calculate)
        main_layout.add_widget(calc_btn)
        
        # 角度ガイドセクション追加
        guide_section = self.create_guide_section()
        main_layout.add_widget(guide_section)
        
        # カメラセクション追加（OpenCV利用可能時のみ）
        if OPENCV_AVAILABLE:
            camera_section = self.create_camera_placeholder()
            main_layout.add_widget(camera_section)
        else:
            no_camera = Label(
                text="📷 カメラ機能: pip install opencv-python が必要",
                size_hint_y=None,
                height=40,
                font_size=12,
                color=(0.7, 0.7, 0.7, 1),
                font_name=FONT_NAME
            )
            main_layout.add_widget(no_camera)
        
        # ステータス表示追加
        self.status_label = Label(
            text="✅ 準備完了",
            size_hint_y=None,
            height=30,
            font_size=12,
            color=(0.2, 0.8, 1, 1),
            font_name=FONT_NAME
        )
        main_layout.add_widget(self.status_label)
        
        # 結果表示セクション追加
        result_section = self.create_result_section()
        main_layout.add_widget(result_section)
        
        # ヘルプセクション追加
        help_section = self.create_help_section()
        main_layout.add_widget(help_section)
        
        # 余白追加
        spacer = Label(text="", size_hint_y=None, height=30)
        main_layout.add_widget(spacer)
        
        # スクロールビューにレイアウトを設定
        scroll.add_widget(main_layout)
        return scroll
    
    def create_header(self):
        """ヘッダーセクション作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=70, spacing=5)
        
        title = Label(
            text="📐 U字溝カットガイド",
            size_hint_y=None,
            height=40,
            font_size=20,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        subtitle = Label(
            text="角度と幅から切断寸法を正確に計算",
            size_hint_y=None,
            height=25,
            font_size=12,
            color=(0.7, 0.7, 0.7, 1),
            font_name=FONT_NAME
        )
        layout.add_widget(subtitle)
        
        return layout
    
    def create_input_section(self):
        """入力セクション作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=130, spacing=8)
        
        # セクションタイトル
        title = Label(
            text="📝 入力項目",
            size_hint_y=None,
            height=25,
            font_size=14,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        # 入力フィールド（グリッドレイアウト）
        input_grid = GridLayout(cols=2, size_hint_y=None, height=75, spacing=10)
        
        # 角度入力
        angle_layout = BoxLayout(orientation='vertical')
        angle_layout.add_widget(Label(
            text="曲げ角度 (°)",
            size_hint_y=None,
            height=25,
            font_size=12,
            font_name=FONT_NAME
        ))
        self.angle_input = TextInput(
            text="135",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=45,
            font_size=14
        )
        self.angle_input.bind(text=self.on_input_change)
        angle_layout.add_widget(self.angle_input)
        input_grid.add_widget(angle_layout)
        
        # 幅入力
        width_layout = BoxLayout(orientation='vertical')
        width_layout.add_widget(Label(
            text="製品幅 (mm)",
            size_hint_y=None,
            height=25,
            font_size=12,
            font_name=FONT_NAME
        ))
        self.width_input = TextInput(
            text="520",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=45,
            font_size=14
        )
        width_layout.add_widget(self.width_input)
        input_grid.add_widget(width_layout)
        
        layout.add_widget(input_grid)
        
        # クイック角度ボタン
        quick_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=5)
        quick_layout.add_widget(Label(
            text="クイック:",
            size_hint_x=None,
            width=70,
            font_size=11,
            font_name=FONT_NAME
        ))
        
        for angle in [90, 120, 135, 150]:
            btn = Button(
                text=f"{angle}°",
                size_hint_x=None,
                width=55,
                font_size=11,
                font_name=FONT_NAME
            )
            btn.bind(on_press=lambda x, a=angle: self.set_quick_angle(a))
            quick_layout.add_widget(btn)
        
        layout.add_widget(quick_layout)
        
        return layout
    
    def create_guide_section(self):
        """角度ガイドセクション作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=220, spacing=5)
        
        # セクションタイトル
        title = Label(
            text="📐 角度ガイド",
            size_hint_y=None,
            height=25,
            font_size=14,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        # 角度ガイド表示
        self.angle_guide = SimpleAngleGuide(size_hint_y=None, height=130)
        layout.add_widget(self.angle_guide)
        
        # スライダーコントロール
        slider_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=60, spacing=3)
        
        # 現在の角度と計算結果表示
        self.angle_display = Label(
            text="角度: 135° | 切断長さ: 216.5mm",
            size_hint_y=None,
            height=20,
            font_size=11,
            font_name=FONT_NAME
        )
        slider_layout.add_widget(self.angle_display)
        
        # 角度調整スライダー
        self.angle_slider = Slider(
            min=30, max=180, value=135, step=1,
            size_hint_y=None, height=25
        )
        self.angle_slider.bind(value=self.on_slider_change)
        slider_layout.add_widget(self.angle_slider)
        
        # スライダー目盛り表示
        scale_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=15)
        for angle in [30, 90, 135, 180]:
            scale_layout.add_widget(Label(
                text=f"{angle}°",
                font_size=9,
                font_name=FONT_NAME
            ))
        slider_layout.add_widget(scale_layout)
        
        layout.add_widget(slider_layout)
        
        return layout
    
    def create_camera_placeholder(self):
        """カメラ機能プレースホルダー作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80, spacing=5)
        
        title = Label(
            text="📷 カメラ機能（準備中）",
            size_hint_y=None,
            height=25,
            font_size=14,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        info = Label(
            text="実際の現場でカメラを使用した角度測定機能を準備中です",
            size_hint_y=None,
            height=30,
            font_size=11,
            color=(0.7, 0.7, 0.7, 1),
            font_name=FONT_NAME
        )
        layout.add_widget(info)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=25, spacing=5)
        
        for label in ["📷 カメラ起動", "📐 角度測定", "📸 撮影"]:
            btn = Button(
                text=label,
                font_size=10,
                font_name=FONT_NAME,
                disabled=True
            )
            button_layout.add_widget(btn)
        
        layout.add_widget(button_layout)
        
        return layout
    
    def create_result_section(self):
        """結果表示セクション作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=110, spacing=5)
        
        # セクションタイトル
        title = Label(
            text="📋 計算結果",
            size_hint_y=None,
            height=25,
            font_size=14,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        # 結果表示グリッド
        result_grid = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        
        # 切断角度結果
        angle_layout = BoxLayout(orientation='vertical')
        angle_layout.add_widget(Label(
            text="切断角度",
            size_hint_y=None,
            height=25,
            font_size=12,
            font_name=FONT_NAME
        ))
        self.result_angle = Label(
            text="67.5°",
            size_hint_y=None,
            height=50,
            font_size=18,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=FONT_NAME
        )
        angle_layout.add_widget(self.result_angle)
        result_grid.add_widget(angle_layout)
        
        # 切断長さ結果
        length_layout = BoxLayout(orientation='vertical')
        length_layout.add_widget(Label(
            text="切断長さ",
            size_hint_y=None,
            height=25,
            font_size=12,
            font_name=FONT_NAME
        ))
        self.result_length = Label(
            text="216.5 mm",
            size_hint_y=None,
            height=50,
            font_size=18,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=FONT_NAME
        )
        length_layout.add_widget(self.result_length)
        result_grid.add_widget(length_layout)
        
        layout.add_widget(result_grid)
        
        return layout
    
    def create_help_section(self):
        """ヘルプセクション作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=180, spacing=5)
        
        # セクションタイトル
        title = Label(
            text="❓ 使い方・計算式",
            size_hint_y=None,
            height=25,
            font_size=14,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        # ヘルプテキスト
        help_text = """🔹 基本操作:
1. 曲げ角度と製品幅を入力
2. 「計算実行」ボタンを押す
3. 切断角度と切断長さを確認

🔹 便利機能:
・クイックボタンで一般的な角度を素早く設定
・スライダーでリアルタイム計算・角度確認

🔹 計算式:
・切断角度 = 90° - (180° - 曲げ角度) ÷ 2
・切断長さ = 製品幅 ÷ tan(切断角度)

🔹 使用例:
135°に曲げる520mm幅の製品
→ 切断角度67.5°、切断長さ216.5mm"""
        
        help_label = Label(
            text=help_text,
            size_hint_y=None,
            height=150,
            font_size=10,
            color=(0.8, 0.8, 0.8, 1),
            text_size=(None, None),
            halign='left',
            valign='top',
            font_name=FONT_NAME
        )
        layout.add_widget(help_label)
        
        return layout
    
    # イベントハンドラーメソッド群
    def set_quick_angle(self, angle):
        """クイック角度設定"""
        self.angle_input.text = str(angle)
        self.angle_slider.value = angle
        self.update_displays(angle)
        
    def on_input_change(self, instance, value):
        """角度入力変更時の処理"""
        try:
            if value and value.strip():
                angle = float(value)
                angle = max(30, min(180, angle))
                self.angle_slider.value = angle
                self.update_displays(angle)
        except ValueError:
            pass  # 無効な入力は無視
        except Exception as e:
            print(f"入力変更エラー: {e}")
    
    def on_slider_change(self, instance, value):
        """スライダー変更時の処理"""
        try:
            angle = int(value)
            self.angle_input.text = str(angle)
            self.update_displays(angle)
        except Exception as e:
            print(f"スライダー変更エラー: {e}")
    
    def update_displays(self, angle):
        """表示内容を更新"""
        try:
            # 角度ガイドを更新
            self.angle_guide.set_angle(angle)
            
            # リアルタイム計算実行
            width_text = self.width_input.text
            if width_text and width_text.strip():
                width = float(width_text)
                
                if angle >= 180:
                    cut_length = 0
                else:
                    half_angle = (180 - angle) / 2
                    cut_angle = 90 - half_angle
                    cut_angle_rad = math.radians(cut_angle)
                    cut_length = width / math.tan(cut_angle_rad)
                
                self.angle_display.text = f"角度: {angle}° | 切断長さ: {cut_length:.1f}mm"
            else:
                self.angle_display.text = f"角度: {angle}° | 切断長さ: ---mm"
                
        except Exception as e:
            print(f"表示更新エラー: {e}")
            self.angle_display.text = f"角度: {angle}° | 切断長さ: エラー"
    
    def calculate(self, instance):
        """メイン計算実行"""
        try:
            # 入力値取得
            angle_text = self.angle_input.text
            width_text = self.width_input.text
            
            if not angle_text or not angle_text.strip():
                self.status_label.text = "❌ 角度を入力してください"
                return
                
            if not width_text or not width_text.strip():
                self.status_label.text = "❌ 幅を入力してください"
                return
            
            angle = float(angle_text)
            width = float(width_text)
            
            # 入力値検証
            if angle <= 0 or angle > 180:
                self.status_label.text = "❌ 角度は1°〜180°で入力してください"
                return
            
            if width <= 0:
                self.status_label.text = "❌ 幅は0より大きい値を入力してください"
                return
            
            # 計算開始表示
            self.status_label.text = "🔄 計算中..."
            
            # 180°の特殊ケース処理
            if angle >= 180:
                self.result_angle.text = "90.0°"
                self.result_length.text = "0.0 mm"
                self.status_label.text = "✅ 計算完了！（直線のため切断なし）"
                return
            
            # 通常の計算処理
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            
            # 結果表示
            self.result_angle.text = f"{cut_angle:.1f}°"
            self.result_length.text = f"{cut_length:.1f} mm"
            
            # スライダーと表示を同期
            self.angle_slider.value = angle
            self.update_displays(angle)
            
            # 完了メッセージ
            self.status_label.text = "✅ 計算完了！"
            
        except ValueError:
            self.status_label.text = "❌ 数値を正しく入力してください"
        except ZeroDivisionError:
            self.status_label.text = "❌ 計算エラー: 角度が90°に近すぎます"
        except Exception as e:
            self.status_label.text = f"❌ 予期しないエラー: {str(e)}"
            print(f"計算エラーの詳細: {e}")

# アプリケーションの起動
if __name__ == '__main__':
    ScrollCutGuideApp().run()