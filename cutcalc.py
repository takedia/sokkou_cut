# -*- coding: utf-8 -*-
"""
U字溝カットガイド - 実働カメラ機能版
OpenCVを使用した実際のカメラ機能を実装

機能:
- リアルタイムカメラプレビュー
- 角度ガイドオーバーレイ
- カメラ撮影機能
- 複数カメラ対応
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.logger import Logger
import math
import os
import numpy as np

# デバッグ用ウィンドウサイズ
Window.size = (400, 700)

# フォント設定
def setup_font():
    try:
        if os.name == 'nt':
            font_paths = [
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/msgothic.ttc"
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    LabelBase.register(name="Japanese", fn_regular=font_path)
                    return "Japanese"
    except Exception as e:
        Logger.info(f"フォント設定エラー: {e}")
    return None

FONT_NAME = setup_font()

# OpenCV設定
try:
    import cv2
    OPENCV_AVAILABLE = True
    Logger.info("OpenCV利用可能")
except ImportError:
    OPENCV_AVAILABLE = False
    Logger.warning("OpenCV利用不可")

class CameraWidget(Image):
    """実働カメラウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.is_playing = False
        self.camera_index = 0
        self.fps = 30
        
    def detect_cameras(self):
        """利用可能なカメラを検出"""
        available_cameras = []
        for i in range(5):  # 最大5台まで検出
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
                Logger.info(f"カメラ {i} 検出")
            else:
                Logger.info(f"カメラ {i} 利用不可")
        return available_cameras
    
    def start_camera(self, camera_index=0):
        """カメラ開始"""
        if not OPENCV_AVAILABLE:
            Logger.error("OpenCVが利用できません")
            return False
        
        try:
            # 既存のカメラを停止
            if self.capture:
                self.capture.release()
            
            Logger.info(f"カメラ {camera_index} 起動試行")
            self.capture = cv2.VideoCapture(camera_index)
            
            if not self.capture.isOpened():
                Logger.error(f"カメラ {camera_index} を開けません")
                return False
            
            # カメラ設定
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # テストフレーム取得
            ret, frame = self.capture.read()
            if not ret:
                Logger.error("カメラからフレームを取得できません")
                self.capture.release()
                return False
            
            self.camera_index = camera_index
            self.is_playing = True
            
            # フレーム更新開始
            Clock.schedule_interval(self.update_frame, 1.0 / self.fps)
            
            Logger.info(f"カメラ {camera_index} 起動成功")
            return True
            
        except Exception as e:
            Logger.error(f"カメラ起動エラー: {e}")
            if self.capture:
                self.capture.release()
                self.capture = None
            return False
    
    def stop_camera(self):
        """カメラ停止"""
        self.is_playing = False
        Clock.unschedule(self.update_frame)
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        # 黒画面に戻す
        self.texture = None
        Logger.info("カメラ停止")
    
    def update_frame(self, dt):
        """フレーム更新"""
        if not self.is_playing or not self.capture:
            return False
        
        try:
            ret, frame = self.capture.read()
            if not ret:
                Logger.warning("フレーム取得失敗")
                return True
            
            # フレームを処理
            frame = cv2.flip(frame, 0)  # 垂直反転（Kivyの座標系に合わせる）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # テクスチャ作成
            h, w, c = frame_rgb.shape
            texture = Texture.create(size=(w, h), colorfmt='rgb')
            texture.blit_buffer(frame_rgb.flatten(), colorfmt='rgb', bufferfmt='ubyte')
            
            # テクスチャを画像に適用
            self.texture = texture
            
            return True
            
        except Exception as e:
            Logger.error(f"フレーム更新エラー: {e}")
            return False
    
    def capture_image(self):
        """現在のフレームをキャプチャ"""
        if not self.capture or not self.is_playing:
            return None
        
        try:
            ret, frame = self.capture.read()
            if ret:
                # タイムスタンプ付きで保存
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                Logger.info(f"画像保存: {filename}")
                return frame
        except Exception as e:
            Logger.error(f"画像キャプチャエラー: {e}")
        
        return None

class AngleGuideOverlay(BoxLayout):
    """角度ガイドオーバーレイ"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 135
        self.bind(size=self.update_overlay)
        
    def set_angle(self, angle):
        self.angle = angle
        self.update_overlay()
        
    def update_overlay(self, *args):
        self.canvas.after.clear()
        
        if self.width == 0 or self.height == 0:
            Clock.schedule_once(lambda dt: self.update_overlay(), 0.1)
            return
        
        try:
            with self.canvas.after:
                # 半透明背景
                Color(0, 0, 0, 0.3)
                Rectangle(pos=self.pos, size=self.size)
                
                # ガイドライン（明るい緑）
                Color(0.2, 1, 0.2, 0.9)
                
                center_x = self.width / 2
                center_y = self.height / 2
                radius = min(self.width, self.height) * 0.3
                
                # 中心点
                Ellipse(pos=(center_x - 8, center_y - 8), size=(16, 16))
                
                # 角度ライン計算
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
                
                # 角度弧
                Color(0.2, 1, 0.2, 0.6)
                arc_radius = radius * 0.7
                for i in range(int(start_angle), int(end_angle) + 1, 2):
                    rad = math.radians(i)
                    x = center_x + arc_radius * math.cos(rad)
                    y = center_y + arc_radius * math.sin(rad)
                    Ellipse(pos=(x - 2, y - 2), size=(4, 4))
                
        except Exception as e:
            Logger.error(f"オーバーレイ描画エラー: {e}")

class CameraGuideApp(App):
    """カメラ機能付きメインアプリ"""
    
    def build(self):
        # メインスクロールビュー
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            scroll_type=['content']
        )
        
        main_layout = BoxLayout(
            orientation='vertical',
            padding=10,
            spacing=8,
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # ヘッダー
        header = self.create_header()
        main_layout.add_widget(header)
        
        # 入力セクション
        input_section = self.create_input_section()
        main_layout.add_widget(input_section)
        
        # 計算ボタン
        calc_btn = Button(
            text="🧮 計算実行",
            size_hint_y=None,
            height=45,
            font_size=14,
            background_color=(0.2, 0.7, 0.2, 1),
            font_name=FONT_NAME
        )
        calc_btn.bind(on_press=self.calculate)
        main_layout.add_widget(calc_btn)
        
        # カメラセクション
        if OPENCV_AVAILABLE:
            camera_section = self.create_camera_section()
            main_layout.add_widget(camera_section)
        else:
            no_camera = Label(
                text="📷 カメラ機能を使用するには 'pip install opencv-python' が必要です",
                size_hint_y=None,
                height=50,
                font_size=11,
                color=(1, 0.3, 0.3, 1),
                font_name=FONT_NAME,
                text_size=(None, None),
                halign='center'
            )
            main_layout.add_widget(no_camera)
        
        # ステータス
        self.status_label = Label(
            text="✅ アプリ起動完了",
            size_hint_y=None,
            height=25,
            font_size=11,
            color=(0.2, 0.8, 1, 1),
            font_name=FONT_NAME
        )
        main_layout.add_widget(self.status_label)
        
        # 結果表示
        result_section = self.create_result_section()
        main_layout.add_widget(result_section)
        
        # 余白
        spacer = Label(text="", size_hint_y=None, height=30)
        main_layout.add_widget(spacer)
        
        scroll.add_widget(main_layout)
        return scroll
    
    def create_header(self):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=50, spacing=3)
        
        title = Label(
            text="📐 U字溝カットガイド（カメラ版）",
            size_hint_y=None,
            height=30,
            font_size=16,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        subtitle = Label(
            text="カメラで角度を測定して切断寸法を計算",
            size_hint_y=None,
            height=17,
            font_size=10,
            color=(0.7, 0.7, 0.7, 1),
            font_name=FONT_NAME
        )
        layout.add_widget(subtitle)
        
        return layout
    
    def create_input_section(self):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=90, spacing=5)
        
        # 入力フィールド
        input_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=8)
        
        # 角度入力
        angle_box = BoxLayout(orientation='vertical')
        angle_box.add_widget(Label(
            text="角度(°)", 
            size_hint_y=None, 
            height=15, 
            font_size=10,
            font_name=FONT_NAME
        ))
        self.angle_input = TextInput(
            text="135",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=40,
            font_size=12
        )
        self.angle_input.bind(text=self.on_input_change)
        angle_box.add_widget(self.angle_input)
        input_row.add_widget(angle_box)
        
        # 幅入力
        width_box = BoxLayout(orientation='vertical')
        width_box.add_widget(Label(
            text="幅(mm)", 
            size_hint_y=None, 
            height=15, 
            font_size=10,
            font_name=FONT_NAME
        ))
        self.width_input = TextInput(
            text="520",
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=40,
            font_size=12
        )
        width_box.add_widget(self.width_input)
        input_row.add_widget(width_box)
        
        layout.add_widget(input_row)
        
        # クイックボタン
        quick_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=25, spacing=3)
        for angle in [90, 120, 135, 150]:
            btn = Button(
                text=f"{angle}°",
                font_size=9,
                font_name=FONT_NAME
            )
            btn.bind(on_press=lambda x, a=angle: self.set_quick_angle(a))
            quick_row.add_widget(btn)
        layout.add_widget(quick_row)
        
        return layout
    
    def create_camera_section(self):
        accordion = Accordion(orientation='vertical', size_hint_y=None, height=300)
        
        camera_item = AccordionItem(title='📷 カメラ角度ガイド（タップして開く）')
        camera_layout = BoxLayout(orientation='vertical', spacing=3, padding=3)
        
        # カメラプレビューエリア
        camera_container = BoxLayout(size_hint_y=0.7)
        
        # カメラウィジェット
        self.camera_widget = CameraWidget()
        camera_container.add_widget(self.camera_widget)
        
        # 角度ガイドオーバーレイ
        self.angle_overlay = AngleGuideOverlay()
        camera_container.add_widget(self.angle_overlay)
        
        camera_layout.add_widget(camera_container)
        
        # 角度制御
        angle_control = self.create_angle_control()
        camera_layout.add_widget(angle_control)
        
        # カメラ操作ボタン
        button_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=30, 
            spacing=2
        )
        
        start_btn = Button(text="📷起動", font_size=9, font_name=FONT_NAME)
        start_btn.bind(on_press=self.start_camera)
        button_layout.add_widget(start_btn)
        
        capture_btn = Button(text="📸撮影", font_size=9, font_name=FONT_NAME)
        capture_btn.bind(on_press=self.capture_image)
        button_layout.add_widget(capture_btn)
        
        stop_btn = Button(text="⏹️停止", font_size=9, font_name=FONT_NAME)
        stop_btn.bind(on_press=self.stop_camera)
        button_layout.add_widget(stop_btn)
        
        guide_calc_btn = Button(text="📐計算", font_size=9, font_name=FONT_NAME)
        guide_calc_btn.bind(on_press=self.calculate_with_guide)
        button_layout.add_widget(guide_calc_btn)
        
        camera_layout.add_widget(button_layout)
        
        camera_item.add_widget(camera_layout)
        accordion.add_widget(camera_item)
        
        return accordion
    
    def create_angle_control(self):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=50, spacing=2)
        
        # 角度表示
        self.angle_display = Label(
            text="角度: 135° | 長さ: 216.5mm",
            size_hint_y=None,
            height=15,
            font_size=9,
            font_name=FONT_NAME
        )
        layout.add_widget(self.angle_display)
        
        # スライダー
        self.angle_slider = Slider(
            min=30, max=180, value=135, step=1,
            size_hint_y=None, height=20
        )
        self.angle_slider.bind(value=self.on_slider_change)
        layout.add_widget(self.angle_slider)
        
        # 目盛り
        scale_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=15)
        for angle in [30, 90, 135, 180]:
            scale_layout.add_widget(Label(
                text=f"{angle}°", 
                font_size=7,
                font_name=FONT_NAME
            ))
        layout.add_widget(scale_layout)
        
        return layout
    
    def create_result_section(self):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80, spacing=3)
        
        title = Label(
            text="📋 計算結果",
            size_hint_y=None,
            height=20,
            font_size=12,
            bold=True,
            font_name=FONT_NAME
        )
        layout.add_widget(title)
        
        result_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=57)
        
        # 切断角度
        angle_result = BoxLayout(orientation='vertical')
        angle_result.add_widget(Label(
            text="切断角度", 
            size_hint_y=0.3, 
            font_size=9,
            font_name=FONT_NAME
        ))
        self.result_angle = Label(
            text="67.5°",
            size_hint_y=0.7,
            font_size=14,
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
            size_hint_y=0.3, 
            font_size=9,
            font_name=FONT_NAME
        ))
        self.result_length = Label(
            text="216.5 mm",
            size_hint_y=0.7,
            font_size=14,
            bold=True,
            color=(0.2, 0.8, 0.2, 1),
            font_name=FONT_NAME
        )
        length_result.add_widget(self.result_length)
        result_layout.add_widget(length_result)
        
        layout.add_widget(result_layout)
        
        return layout
    
    # イベントハンドラー
    def set_quick_angle(self, angle):
        self.angle_input.text = str(angle)
        self.angle_slider.value = angle
        self.update_displays(angle)
    
    def on_input_change(self, instance, value):
        try:
            if value:
                angle = float(value)
                angle = max(30, min(180, angle))
                self.angle_slider.value = angle
                self.update_displays(angle)
        except:
            pass
    
    def on_slider_change(self, instance, value):
        angle = int(value)
        self.angle_input.text = str(angle)
        self.update_displays(angle)
    
    def update_displays(self, angle):
        # 角度ガイド更新
        if hasattr(self, 'angle_overlay'):
            self.angle_overlay.set_angle(angle)
        
        # リアルタイム計算
        try:
            width = float(self.width_input.text) if self.width_input.text else 520
            
            if angle >= 180:
                cut_length = 0
            else:
                half_angle = (180 - angle) / 2
                cut_angle = 90 - half_angle
                cut_angle_rad = math.radians(cut_angle)
                cut_length = width / math.tan(cut_angle_rad)
            
            self.angle_display.text = f"角度: {angle}° | 長さ: {cut_length:.1f}mm"
        except:
            self.angle_display.text = f"角度: {angle}° | 長さ: ---mm"
    
    def calculate(self, instance):
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
                self.status_label.text = "✅ 完了！（直線）"
                return
            
            half_angle = (180 - angle) / 2
            cut_angle = 90 - half_angle
            cut_angle_rad = math.radians(cut_angle)
            cut_length = width / math.tan(cut_angle_rad)
            
            self.result_angle.text = f"{cut_angle:.1f}°"
            self.result_length.text = f"{cut_length:.1f} mm"
            
            self.angle_slider.value = angle
            self.update_displays(angle)
            
            self.status_label.text = "✅ 計算完了！"
            
        except ValueError:
            self.status_label.text = "❌ 数値を正しく入力してください"
        except Exception as e:
            self.status_label.text = f"❌ エラー: {str(e)}"
    
    def calculate_with_guide(self, instance):
        angle = self.angle_slider.value
        self.angle_input.text = str(int(angle))
        self.calculate(instance)
    
    # カメラ機能
    def start_camera(self, instance):
        if not OPENCV_AVAILABLE:
            self.status_label.text = "❌ OpenCVが必要です"
            return
        
        # 利用可能なカメラを検出
        cameras = self.camera_widget.detect_cameras()
        if not cameras:
            self.status_label.text = "❌ カメラが見つかりません"
            return
        
        # 最初のカメラで起動試行
        if self.camera_widget.start_camera(cameras[0]):
            self.status_label.text = f"📷 カメラ{cameras[0]}開始"
        else:
            self.status_label.text = "❌ カメラ開始失敗"
    
    def stop_camera(self, instance):
        if hasattr(self, 'camera_widget'):
            self.camera_widget.stop_camera()
            self.status_label.text = "⏹️ カメラ停止"
    
    def capture_image(self, instance):
        if hasattr(self, 'camera_widget'):
            frame = self.camera_widget.capture_image()
            if frame is not None:
                self.status_label.text = "📸 撮影完了！"
            else:
                self.status_label.text = "❌ 撮影失敗"

if __name__ == '__main__':
    CameraGuideApp().run()
