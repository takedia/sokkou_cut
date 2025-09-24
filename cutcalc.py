# cutcalc.py — Android対応：撮影(カメラ)＋画像読込(ファイルチューザー)付き
# 1行スライダー / 左=90→180°・右=90→0° / ボタン押下で計算

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
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
    OPENCV = True
except Exception:
    Logger.info("OpenCV: not available")

PLYER = False
try:
    from plyer import camera as plyer_camera
    from plyer import filechooser as plyer_filechooser
    PLYER = True
except Exception:
    Logger.info("Plyer: not available")

# Android permission helper
def ensure_android_permissions():
    if platform != "android":
        return
    try:
        from android.permissions import request_permissions, Permission
        perms = [Permission.CAMERA]
        # Android 13+ は READ_MEDIA_IMAGES、12以下は READ_EXTERNAL_STORAGE
        try:
            import jnius
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            sdk = Build.VERSION.SDK_INT
        except Exception:
            sdk = 33
        if sdk >= 33:
            perms += [Permission.READ_MEDIA_IMAGES]
        else:
            perms += [Permission.READ_EXTERNAL_STORAGE]
        request_permissions(perms)
    except Exception as e:
        Logger.warning(f"Permission request failed: {e}")

# ====== UI colors/fonts ======
Window.size = (420, 760)  # PC調整用（Androidでは無視）
BG=(0.20,0.22,0.42,1)
CARD=(1,1,1,0.13); CARD_BG2=(0,0,0,0.10)
TEXT=(1,1,1,1); SUBTEXT=(1,1,1,0.72)
ACCENT=(0.32,0.86,0.44,1); ACCENT_SOFT=(0.82,1.00,0.60,0.95)
BTN_BG=(0.12,0.42,0.18,1); INPUT_BG=(1,1,1,0.10)

def setup_font():
    try:
        for p in [r"C:/Windows/Fonts/meiryo.ttc",
                  r"C:/Windows/Fonts/YuGothM.ttc",
                  r"C:/Windows/Fonts/msgothic.ttc"]:
            if os.path.exists(p):
                LabelBase.register(name="JP", fn_regular=p); return "JP"
        for d in ["/usr/share/fonts","/usr/local/share/fonts",
                  os.path.expanduser("~/.local/share/fonts"),
                  "/System/Library/Fonts","/Library/Fonts"]:
            for pat in ["**/NotoSansJP*.ttf","**/NotoSansCJKjp*.otf","**/SourceHanSansJP*.otf"]:
                fs = glob(os.path.join(d, pat), recursive=True)
                if fs: LabelBase.register(name="JP", fn_regular=fs[0]); return "JP"
    except Exception as e:
        Logger.warning(f"Font setup failed: {e}")
    return "Roboto"
FONT_NAME = setup_font() or "Roboto"

def JLabel(**kw):
    kw.setdefault("font_name",FONT_NAME); kw.setdefault("color",TEXT); return Label(**kw)
def style_textinput(ti:TextInput):
    ti.background_color=INPUT_BG; ti.foreground_color=TEXT; ti.cursor_color=TEXT
    ti.halign="center"; ti.font_name=FONT_NAME; ti.font_size=16; ti.padding=[10,8]
    def _fix(*_): ti.padding=[10, max(0,(ti.height-ti.line_height)/2)]
    ti.bind(size=_fix); _fix()

class Card(BoxLayout):
    def __init__(self, radius=18, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*CARD_BG2); self._shadow=RoundedRectangle(radius=[radius+2],pos=self.pos,size=self.size)
            Color(*CARD);     self._rect  =RoundedRectangle(radius=[radius],  pos=self.pos,size=self.size)
        self.bind(pos=self._upd, size=self._upd)
    def _upd(self,*_):
        self._shadow.pos,self._shadow.size=self.pos,self.size
        self._rect.pos,self._rect.size=self.pos,self.size

# ====== Camera preview (PC/OpenCV用). Androidは静止画表示に切替 ======
class CameraWidget(Image):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.capture=None; self.is_playing=False; self.fps=30
        self.fit_mode="contain"  # ダミー属性（デザイン整合）
    def start(self,index=0):
        if platform == "android":
            # AndroidではOpenCVのライブプレビューは使わず、撮影/画像表示のみにする
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
        if self.width<=0 or self.height<=0: return
        x0,y0=self.x,self.y; x1,y1=self.right,self.top
        cx=(x0+x1)/2.0; cy=(y0+y1)/2.0 + self.center_bias*self.height
        lx,ly=self._edge_point(cx,cy,self.left_angle,x0,y0,x1,y1)
        rx,ry=self._edge_point(cx,cy,self.right_angle,x0,y0,x1,y1)
        with self.canvas.after:
            Color(*ACCENT_SOFT)
            Line(points=[cx,cy,lx,ly],width=self.line_width)
            Line(points=[cx,cy,rx,ry],width=self.line_width)
            Color(0.95,1.0,0.8,0.95)
            Ellipse(pos=(cx-3,cy-3), size=(6,6))

# ====== App ======
class CameraGuideApp(App):
    title = "側溝カット：Android対応版"
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
            self.status.text=f"表示失敗: {e}"

    # ====== PCプレビューON/OFF ======
    def toggle_preview(self, *_):
        if platform == "android":
            self.status.text="Androidは静止画表示のみ（撮影/読込をご利用ください）"
            return
        if getattr(self.camera_view, "is_playing", False):
            self.camera_view.stop()
            self.status.text="プレビュー停止"
        else:
            ok = self.camera_view.start(0)
            self.status.text = "プレビュー開始" if ok else "開始失敗"

if __name__ == "__main__":
    CameraGuideApp().run()