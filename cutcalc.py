# -*- coding: utf-8 -*-
"""
U字溝カットガイド - 日本語対応カメラ機能付き版
Windows環境での文字化け対策とカメラ機能を含む完全版

解決した問題:
1. 日本語文字化け → UTF-8エンコーディング + フォント設定
2. カメラエラー → 適切なエラーハンドリング + 代替手段
3. Windows互換性 → OpenCV-pythonで解決
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.logger import Logger
import math
import os
import sys

# 日本語フォント設定
def setup_font():
    """日本語フォント設定"""
    try:
        if os.name == 'nt':  # Windows
            font_paths = [
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/msgothic.ttc",
                "C:/Windows/Fonts/NotoSansCJK-Regular.ttc"
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    LabelBase.register(name="Japanese", fn_regular=font_path)
                    return "Japanese"
    except Exception as e:
        Logger.info(f"フォント設定: {e}")
    return None

FONT_NAME = setup_font()

# カメラ機能のセットアップ
try:
    import cv2
    OPENCV_AVAILABLE = True
    Logger.info("OpenCV利用可能")
except ImportError:
    OPENCV_AVAILABLE = False
    Logger.info("OpenCV利用不可")

class CameraWidget(Image):
    """OpenCVを使用したカメラウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.is_playing = False
        
    def start_camera(self):
        """カメラ開始"""
        if not OPENCV_AVAILABLE:
            Logger.error("OpenCVが利用できません")
            return False
            
        try:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                Logger.error("カメラを開けません")
                return False
                
            self.is_playing = True
            Clock.schedule_interval(self.update_frame, 1.0/30.0)  # 30 FPS
            Logger.info("カメラ開始成功")
            return True
            
        except Exception as e:
            Logger.error(f"カメラ開始エラー: {e}")
            return False
    
    def stop_camera(self):
        """カメラ停止"""
        self.is_playing = False
        Clock.unschedule(self.update_frame)
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        # 黒い画面に戻す
        self.texture = None
        Logger.info("カメラ停止")
    
    def update_frame(self, dt):
        """フレーム更新"""
        if not self.is_playing or not self.capture:
            return False
            
        try:
            ret, frame = self.capture.read()
            if not ret:
                return True
                
            # OpenCVフレームをKivyテクスチャに変換
            frame = cv2.flip(frame, 0)  # 垂直反転
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR → RGB
            
            # テクスチャ作成
            h, w = frame.shape[:2]
            texture = Texture.create(size=(w, h), colorfmt='rgb')
            texture.blit_buffer(frame.flatten(), colorfmt='rgb', bufferfmt='ubyte')
            
            # テクスチャを適用
            self.texture = texture
            
            return True
            
        except Exception as e:
            Logger.error(f"フレーム更新エラー: {e}")
            return False
    
    def capture_image(self):
        """画像キャプチャ"""
        if not self.capture:
            return None
            
        try:
            ret, frame = self.capture.read()
            if ret:
                return frame
        except Exception as e:
            Logger.error(f"画像キャプチャエラー: {e}")
        
        return None

class AngleGuideOverlay(BoxLayout):
    """角度ガイドオーバーレイ"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 180
        
    def set_angle(self, angle):
        """角度設定"""
        self.angle = angle
        self.update_guide()
        
    def update_guide(self, *args):
        """ガイド更新"""
        self.canvas.after.clear()
        
        if self.width == 0 or self.height == 0:
            Clock.schedule_once(lambda dt: self.update_guide(), 0.1)
            return
            
        with self.canvas.after:
            # 半透明背景
            Color(0, 0, 0, 0.3)
            Rectangle(pos=self.pos, size=self.size)
            
            # ガイドライン
            Color(0.2, 1, 0.2, 0.9)  # 明るい緑
            
            center_x = self.width / 2
            center_y = self.height / 2
            radius = min(self.width, self.height) * 0.3
            
            # 中心点
            Ellipse(pos=(center_x - 6, center_y - 6), size=(12, 12))
            
            # 角度ライン
            start_angle = (180 - self.angle) / 2
            end_angle = start_angle + self.angle
            
            # 左ライン
            left_rad = math.radians(start_angle)
            left_x = center_x + radius * math.cos(left_rad)
            left_y = center_y + radius * math.sin(left_rad)
            Line(points=[center_x, center_y, left_x, left_y], width=4)
            
            # 右ライン
            right_rad = math.radians(end_angle)
            right_x = center_x + radius * math.cos(right_rad)
            right_y = center_y + radius * math.sin(right_rad)
            Line(points=[center_x, center_y, right_x, right_y], width=4)
            
            # 角度表示用の背景
            Color(0, 0, 0, 0.7)
            rect_x = center_x - 40
            rect_y = center_y + radius + 10
            Rectangle(pos=(rect_x, rect_y), size=(80, 30))
            
            # 角度テキストは別途Labelで表示

class CutGuideApp(App):
    """メインアプリケーション"""
    
    def build(self):
        """UI構築"""
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # タイトル
        title = Label(
            text="📐 U字溝カットガイド v2.5",
            size_hint_y=None,
            height=50,
            font_size=20,
            bold=True,
            font_name=FONT_NAME
        )
        main_layout.add_widget(title)
        
        # 説明
        info_text = "カメラで角度を測定し、切断角度・長さを計算します"
        if not OPENCV_AVAILABLE:
            info_text += "\n※ カメラ機能を使用するには 'pip install opencv-python' が必要です"
        
        info = Label(
            text=info_text,
            size_hint_y=None,
            height=60,
            font_size=12,
            color=(0.8, 0.8, 0.8, 1),
            font_name=FONT_NAME
        )
        main_layout.add_widget(info)
        
        # 入力セクション
        input_section = self.create_input_section()
        main_layout.add_widget(input_section)
        
        # 計算ボタン
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
        
        # カメラセクション
        camera_section = self.create_camera_section()
        main_layout.add_widget(camera_section)
        
        # ステータス
        self.status_label = Label(
            text="✅ アプリ起動完了",
            size_hint_y=None,
            height=30,
            color=(0.2, 0.8, 1, 1),
            font_name=FONT_NAME
        )
        main_layout.add_widget(self.status_label)
        
        # 結果表示
        result_section = self.create_result_section()
        main_layout.add_widget(result_section)
        
        return main_layout
    
    def create_input_section(self):
        """入力セクション作成"""
        layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10)
        
        # 角度入力
        angle_box = BoxLayout(orientation='vertical')
        angle_box.add_widget(Label(
            text="📐 曲げ角度 (°)", 
            size_hint_y=None, 
            height=25,
            font_name=FONT_NAME
        ))
        self.angle_input = TextInput(
            text="135",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=40,
            font_size=14
        )
        angle_box.add_widget(self.angle_input)
        layout.add_widget(angle_box)
        
        # 幅入力
        width_box = BoxLayout(orientation='vertical')
        width_box.add_widget(Label(
            text="📏 製品幅 (mm)", 
            size_hint_y=None, 
            height=25,
            font_name=FONT_NAME
        ))
        self.width_input = TextInput(
            text="520",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=40,
            font_size=14
        )
        width_box.add_widget(self.width_input)
        layout.add_widget(width_box)
        
        return layout
    
    def create_camera_section(self):
        """カメラセクション作成"""
        accordion = Accordion(orientation='vertical', size_hint_y=None, height=350)
        
        camera_item = AccordionItem(title='📷 カメラ角度ガイド')
        camera_layout = BoxLayout(orientation='vertical', spacing=5, padding=5)
        
        # カメラ表示エリア
        camera_container = BoxLayout(size_hint_y=0.7)
        
        if OPENCV_AVAILABLE:
            # OpenCVカメラウィジェット
            self.camera_widget = CameraWidget()
            camera_container.add_widget(self.camera_widget)
            
            # 角度ガイドオーバーレイ
            self.angle_overlay = AngleGuideOverlay()
            camera_container.add_widget(self.angle_overlay)
        else:
            # カメラ利用不可の場合
            placeholder = Label(
                text="📷 カメラ機能を使用するには\npip install opencv-python\nを実行してください",
                font_name=FONT_NAME
            )
            camera_container.add_widget(placeholder)
        
        camera_layout.add_widget(camera_container)
        
        # 角度制御
        angle_control = self.create_angle_control()
        camera_layout.add_widget(angle_control)
        
        # カメラ操作ボタン
        if OPENCV_AVAILABLE:
            button_layout = BoxLayout(
                orientation='horizontal', 
                size_hint_y=None, 
                height=40, 
                spacing=5
            )
            
            start_btn = Button(text="📷 開始", font_name=FONT_NAME)
            start_btn.bind(on_press=self.start_camera)
            button_layout.add_widget(start_btn)
            
            capture_btn = Button(text="📸 撮影", font_name=FONT_NAME)
            capture_btn.bind(on_press=self.capture_image)
            button_layout.add_widget(capture_btn)
            
            stop_btn = Button(text="⏹️ 停止", font_name=FONT_NAME)
            stop_btn.bind(on_press=self.stop_camera)
            button_layout.add_widget(stop_btn)
            
            guide_calc_btn = Button(text="📐 この角度で計算", font_name=FONT_NAME)
            guide_calc_btn.bind(on_press=self.calculate_with_guide)
            button_layout.add_widget(guide_calc_btn)
            
            camera_layout.add_widget(button_layout)
        
        camera_item.add_widget(camera_layout)
        accordion.add_widget(camera_item)
        
        return accordion
    
    def create_angle_control(self):
        """角度制御作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=70, spacing=3)
        
        # 角度表示
        info_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=25)
        
        self.angle_display = Label(
            text="目標角度: 135°", 
            size_hint_x=0.5, 
            font_size=12,
            font_name=FONT_NAME
        )
        info_layout.add_widget(self.angle_display)
        
        self.length_display = Label(
            text="切断長さ: 216.5mm", 
            size_hint_x=0.5, 
            font_size=12,
            font_name=FONT_NAME
        )
        info_layout.add_widget(self.length_display)
        
        layout.add_widget(info_layout)
        
        # スライダー
        self.angle_slider = Slider(
            min=30, max=180, value=135, step=1,
            size_hint_y=None, height=25
        )
        self.angle_slider.bind(value=self.on_slider_change)
        layout.add_widget(self.angle_slider)
        
        # スライダー目盛り
        scale_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=20)
        for angle in [30, 90, 135, 180]:
            scale_layout.add_widget(Label(
                text=f"{angle}°", 
                font_size=10,
                font_name=FONT_NAME
            ))
        layout.add_widget(scale_layout)
        
        return layout
    
    def create_result_section(self):
        """結果表示セクション作成"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=90, spacing=5)
        
        title = Label(
            text="📋 計算結果",
            size_hint_y=None,
            height=25,
            font_size=14,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        result_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        
        # 切断角度
        angle_result = BoxLayout(orientation='vertical')
        angle_result.add_widget(Label(
            text="切断角度", 
            size_hint_y=0.4, 
            font_size=12,
            font_name=FONT_NAME
        ))
        self.result_angle = Label(
            text="67.5°",
            size_hint_y=0.6,
            font_size=16,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=FONT_NAME
        )
        angle_result.add_widget(self.result_angle)
        result_layout.add_widget(angle_result)
        
        # 切断長さ
        length_result = BoxLayout(orientation='vertical')
        length_result.add_widget(Label(
            text="切断長さ", 
            size_hint_y=0.4, 
            font_size=12,
            font_name=FONT_NAME
        ))
        self.result_length = Label(
            text="216.5 mm",
            size_hint_y=0.6,
            font_size=16,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=FONT_NAME
        )
        length_result.add_widget(self.result_length)
        result_layout.add_widget(length_result)
        
        layout.add_widget(result_layout)
        
        return layout
    
    # イベントハンドラー
    def on_slider_change(self, instance, value):
        """スライダー変更"""
        angle = int(value)
        self.angle_input.text = str(angle)
        self.angle_display.text = f"目標角度: {angle}°"
        
        # ガイドオーバーレイ更新
        if OPENCV_AVAILABLE and hasattr(self, 'angle_overlay'):
            self.angle_overlay.set_angle(angle)
        
        # リアルタイム計算
        self.calculate_realtime(angle)
    
    def calculate_realtime(self, angle):
        """リアルタイム計算"""
        try:
            width = float(self.width_input.text) if self.width_input.text else 520
            
            if angle >= 180:
                self.length_display.text = "切断長さ: 0.0mm"
                return
            
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            
            self.length_display.text = f"切断長さ: {cut_length:.1f}mm"
            
        except:
            self.length_display.text = "切断長さ: ---mm"
    
    def calculate(self, instance):
        """メイン計算"""
        try:
            angle = float(self.angle_input.text)
            width = float(self.width_input.text)
            
            if angle <= 0 or angle > 180:
                self.status_label.text = "❌ 角度は1°〜180°で入力してください"
                return
            
            if width <= 0:
                self.status_label.text = "❌ 幅は0より大きい値を入力してください"
                return
            
            self.status_label.text = "🔄 計算中..."
            
            if angle >= 180:
                self.result_angle.text = "90.0°"
                self.result_length.text = "0.0 mm"
                self.status_label.text = "✅ 完了！（直線のため切断なし）"
                return
            
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            
            self.result_angle.text = f"{cut_angle:.1f}°"
            self.result_length.text = f"{cut_length:.1f} mm"
            
            # スライダーも更新
            self.angle_slider.value = angle
            
            self.status_label.text = "✅ 計算完了！"
            
        except ValueError:
            self.status_label.text = "❌ 数値を正しく入力してください"
        except Exception as e:
            self.status_label.text = f"❌ エラー: {str(e)}"
    
    def calculate_with_guide(self, instance):
        """ガイド角度で計算"""
        angle = self.angle_slider.value
        self.angle_input.text = str(int(angle))
        self.calculate(instance)
    
    # カメラ機能
    def start_camera(self, instance):
        """カメラ開始"""
        if not OPENCV_AVAILABLE:
            self.status_label.text = "❌ OpenCVがインストールされていません"
            return
        
        if hasattr(self, 'camera_widget'):
            if self.camera_widget.start_camera():
                self.status_label.text = "📷 カメラ開始しました"
            else:
                self.status_label.text = "❌ カメラを開始できませんでした"
    
    def stop_camera(self, instance):
        """カメラ停止"""
        if hasattr(self, 'camera_widget'):
            self.camera_widget.stop_camera()
            self.status_label.text = "⏹️ カメラを停止しました"
    
    def capture_image(self, instance):
        """画像撮影"""
        if hasattr(self, 'camera_widget'):
            frame = self.camera_widget.capture_image()
            if frame is not None:
                self.status_label.text = "📸 撮影完了！角度を調整してください"
            else:
                self.status_label.text = "❌ 撮影に失敗しました"


if __name__ == '__main__':
    CutGuideApp().run()