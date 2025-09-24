# cutcalc.py — 1行版（左S=左ガイド90→180 / 右S=右ガイド90→0）

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
<<<<<<< Updated upstream
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
=======
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
>>>>>>> Stashed changes
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.logger import Logger
<<<<<<< Updated upstream
import os, math
from glob import glob
=======
import math
import os
from glob import glob
import numpy as np
>>>>>>> Stashed changes

Window.size = (420, 760)

# ---------- Font ----------
def setup_font():
    try:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # 優先的に環境変数で指定されたフォントを利用
        env_font = os.environ.get("KIVY_JP_FONT")
        if env_font and os.path.exists(env_font):
            LabelBase.register(name="Japanese", fn_regular=env_font)
            Logger.info(f"日本語フォント: 環境変数から {env_font}")
            return "Japanese"

        font_paths = []

        if os.name == 'nt':
            font_paths.extend([
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/msgothic.ttc",
                "C:/Windows/Fonts/YuGothM.ttc",
            ])
        else:
            search_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.local/share/fonts"),
                "/System/Library/Fonts",
                "/Library/Fonts",
            ]

            patterns = [
                "**/NotoSansCJK*.ttc",
                "**/NotoSansCJKjp*.otf",
                "**/NotoSansJP*.otf",
                "**/NotoSansJP*.ttf",
                "**/SourceHanSansJP*.otf",
                "**/SourceHanSansJP*.ttc",
                "**/ipagp.ttf",
                "**/ipam.ttf",
                "**/ipaexg.ttf",
                "**/TakaoPGothic.ttf",
                "**/HiraginoSans-*.ttc",
            ]

            for directory in search_dirs:
                if not os.path.isdir(directory):
                    continue
                for pattern in patterns:
                    font_paths.extend(glob(os.path.join(directory, pattern), recursive=True))

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    LabelBase.register(name="Japanese", fn_regular=font_path)
                    Logger.info(f"日本語フォント: {font_path}")
                    return "Japanese"
                except Exception as font_error:
                    Logger.warning(f"フォント登録失敗: {font_path} ({font_error})")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    except Exception as e:
        Logger.warning(f"Font setup failed: {e}")
    return "Roboto"
FONT_NAME = setup_font() or "Roboto"

# ---------- Colors ----------
BG=(0.20,0.22,0.42,1)
CARD=(1,1,1,0.13); CARD_BG2=(0,0,0,0.10)
TEXT=(1,1,1,1); SUBTEXT=(1,1,1,0.72)
ACCENT=(0.32,0.86,0.44,1); ACCENT_SOFT=(0.82,1.00,0.60,0.95)
BTN_BG=(0.12,0.42,0.18,1); INPUT_BG=(1,1,1,0.10)

# ---------- Card ----------
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

# ---------- Camera ----------
try:
    import cv2; OPENCV=True
except Exception:
    OPENCV=False; Logger.warning("OpenCV unavailable.")
class CameraWidget(Image):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.capture=None; self.is_playing=False; self.fps=30
    def start(self,index=0):
        if not OPENCV: return False
        self.capture=cv2.VideoCapture(index)
        if not self.capture.isOpened(): return False
        self.is_playing=True; Clock.schedule_interval(self._update,1.0/self.fps); return True
    def stop(self):
        self.is_playing=False; Clock.unschedule(self._update)
        if self.capture: self.capture.release(); self.capture=None
        self.texture=None
    def _update(self,dt):
        if not(self.capture and self.is_playing): return
        ok, frame = self.capture.read()
        if not ok:
            return
        frame=cv2.flip(frame,0); frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        h,w=frame.shape[:2]; tex=Texture.create(size=(w,h), colorfmt='rgb')
        tex.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        self.texture=tex

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
# ---------- Overlay ----------
class AngleGuideOverlay(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.left_angle=135.0   # 左ガイド（90..180）
        self.right_angle=45.0   # 右ガイド（90..0）
        self.length_ratio=0.84
        self.center_bias=-0.18
        self.line_width=1.6     # 線を少し細く
        self.bind(size=self.update_overlay, pos=self.update_overlay)
    def set_angles(self, left_deg, right_deg):
        self.left_angle=float(left_deg); self.right_angle=float(right_deg); self.update_overlay()
    def _edge_point(self,cx,cy,deg,x0,y0,x1,y1):
        rad=math.radians(deg); dx,dy=math.cos(rad),math.sin(rad); ts=[]
        if dx>0: ts.append((x1-cx)/dx)
        elif dx<0: ts.append((x0-cx)/dx)
        if dy>0: ts.append((y1-cy)/dy)
        elif dy<0: ts.append((y0-cy)/dy)
        t_edge=min([t for t in ts if t>0], default=0.0)
        t=max(0.0,min(1.0,self.length_ratio))*t_edge
        return cx+dx*t, cy+dy*t
    def update_overlay(self,*_):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
class AngleGuideOverlay(Widget):
    """角度ガイドオーバーレイ"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 135
        self.bind(size=self.update_overlay, pos=self.update_overlay)
        
    def set_angle(self, angle):
        self.angle = angle
        self.update_overlay()
        
    def update_overlay(self, *args):
>>>>>>> Stashed changes
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

# ---------- helpers ----------
def JLabel(**kw):
    kw.setdefault("font_name",FONT_NAME); kw.setdefault("color",TEXT); return Label(**kw)
def style_textinput(ti:TextInput):
    ti.background_color=INPUT_BG; ti.foreground_color=TEXT; ti.cursor_color=TEXT
    ti.halign="center"; ti.font_name=FONT_NAME; ti.font_size=16; ti.padding=[10,8]
    def _fix(*_): ti.padding=[10, max(0,(ti.height-ti.line_height)/2)]
    ti.bind(size=_fix); _fix()

# ---------- App ----------
class CameraGuideApp(App):
    def build(self):
<<<<<<< Updated upstream
        Window.clearcolor=BG

        root=FloatLayout()
        scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,size_hint=(1,1))
        Clock.schedule_once(lambda *_: setattr(scroll,"scroll_y",1),0)

        # 余白を少し詰める
        main=BoxLayout(orientation='vertical',padding=12,spacing=8,size_hint_y=None)
        main.bind(minimum_height=main.setter('height'))

        # タイトル
        tcard=Card(orientation='vertical',padding=10,size_hint_y=None,height=86)
        tcard.add_widget(JLabel(text="U字溝カットガイド",font_size=22,bold=True))
        tcard.add_widget(JLabel(text="左右対称 開閉マッピング",font_size=11,color=SUBTEXT))
        main.add_widget(tcard)

        # 入力
        icard=Card(orientation='horizontal',padding=8,spacing=10,size_hint_y=None,height=90)
        colL=BoxLayout(orientation='vertical',size_hint_x=.5,spacing=4)
        colL.add_widget(JLabel(text="角度(°)",font_size=12,color=SUBTEXT))
        self.angle_input=TextInput(text="90",input_filter='float',multiline=False)
        style_textinput(self.angle_input); self.angle_input.readonly=True
        colL.add_widget(self.angle_input)
        colR=BoxLayout(orientation='vertical',size_hint_x=.5,spacing=4)
        colR.add_widget(JLabel(text="幅(mm)",font_size=12,color=SUBTEXT))
        self.width_input=TextInput(text="520",input_filter='float',multiline=False)
        style_textinput(self.width_input); colR.add_widget(self.width_input)
        icard.add_widget(colL); icard.add_widget(colR); main.add_widget(icard)

        # ボタン
        btn=Button(text="計算する",size_hint_y=None,height=44,
                   background_normal="",background_down="",background_color=(0,0,0,0),
                   color=TEXT,font_name=FONT_NAME)
        with btn.canvas.before:
            Color(*BTN_BG); btn._rect=RoundedRectangle(radius=[14],pos=btn.pos,size=btn.size)
        btn.bind(pos=lambda *a:setattr(btn._rect,"pos",btn.pos),
                 size=lambda *a:setattr(btn._rect,"size",btn.size),
                 on_press=self.calculate_from_manual)
        main.add_widget(btn)

        # カメラ＋ガイド
        cam_card=Card(orientation='vertical',padding=0,size_hint_y=None,height=240)
        cam_area=FloatLayout()
        self.camera_view=CameraWidget(size_hint=(1,1),pos_hint={"x":0,"y":0},fit_mode="contain")
        cam_area.add_widget(self.camera_view)
        self.overlay=AngleGuideOverlay(size_hint=(1,1),pos_hint={"x":0,"y":0})
        cam_area.add_widget(self.overlay)
        cam_card.add_widget(cam_area); main.add_widget(cam_card)

        # ---- スライダー（1行：左右対称マッピング）----
        s_card=Card(orientation='vertical',padding=8,size_hint_y=None,height=96)
        self.info_label=JLabel(text="左:135.0°  右:45.0°  |  開き角:90.0°  長さ:--- mm",font_size=12,color=SUBTEXT)
        s_card.add_widget(self.info_label)

        row=BoxLayout(orientation='horizontal',size_hint_y=None,height=30,spacing=10)

        # 左＝左バー（0..100）→ 左角=90+0.9×値（90..180）
        left_col=BoxLayout(orientation='horizontal',spacing=6,size_hint_x=.5)
        left_col.add_widget(JLabel(text="左バー",font_size=11,color=SUBTEXT,size_hint_x=None,width=48))
        self.left_slider=Slider(min=0,max=100,value=50,step=1)
        left_col.add_widget(self.left_slider)

        # 右＝右バー（0..100）→ 右角=90-0.9×値（90..0）
        right_col=BoxLayout(orientation='horizontal',spacing=6,size_hint_x=.5)
        right_col.add_widget(JLabel(text="右バー",font_size=11,color=SUBTEXT,size_hint_x=None,width=48))
        self.right_slider=Slider(min=0,max=100,value=50,step=1)
        right_col.add_widget(self.right_slider)

        row.add_widget(left_col); row.add_widget(right_col)
        s_card.add_widget(row); main.add_widget(s_card)

        # 結果
        res=Card(orientation='horizontal',padding=10,spacing=16,size_hint_y=None,height=86)
        left=BoxLayout(orientation='vertical',spacing=2)
        left.add_widget(JLabel(text="切断角度",font_size=12,color=SUBTEXT))
        self.res_angle=JLabel(text="--.-°",font_size=20,bold=True,color=ACCENT); left.add_widget(self.res_angle)
        right=BoxLayout(orientation='vertical',spacing=2)
        right.add_widget(JLabel(text="切断長さ",font_size=12,color=SUBTEXT))
        self.res_len=JLabel(text="--- mm",font_size=20,bold=True,color=ACCENT); right.add_widget(self.res_len)
        res.add_widget(left); res.add_widget(right); main.add_widget(res)

        # ステータス（見切れにくく）
        self.status=JLabel(text="",font_size=10,color=SUBTEXT)
        main.add_widget(self.status)
        main.add_widget(Widget(size_hint_y=None,height=10))

        # イベント
        self.left_slider.bind(value=self.on_left_change)
        self.right_slider.bind(value=self.on_right_change)

        self._update_overlay_and_info()
        scroll.add_widget(main); root.add_widget(scroll); return root

    # ---- 角度マッピング ----
    def _left_angle_from_slider(self):
        # 左S 0..100 → 左角 180..90 
        return 180.0 - 0.9 * float(self.left_slider.value)

    def _right_angle_from_slider(self):
        # 右S: 0..100 → 90..0
        return 90.0 - 0.9 * float(self.right_slider.value)

    def on_left_change(self, inst, val):
        self._update_overlay_and_info()

    def on_right_change(self, inst, val):
        self._update_overlay_and_info()

    def _update_overlay_and_info(self):
        L = self._left_angle_from_slider()   # 左ガイド（90..180）
        R = self._right_angle_from_slider()  # 右ガイド（90..0）
        self.overlay.set_angles(L, R)

        open_angle = L - R  # 対称なので常に 0..180 に収まる
        self.angle_input.text = f"{open_angle:.1f}"
        self.info_label.text = f"左:{L:.1f}°  右:{R:.1f}°  |  開き角:{open_angle:.1f}°  長さ:{self._calc_length(open_angle)}"

    def _calc_length(self, open_angle):
        try:
            width = float(self.width_input.text) if self.width_input.text else 520.0
        except:
            width = 520.0
        cut_angle = open_angle / 2.0
        if cut_angle <= 0:
            return "--- mm"
        length = width / math.tan(math.radians(cut_angle))
        return f"{length:.1f} mm"

    def calculate_from_manual(self, *_):
        try: open_angle=float(self.angle_input.text)
        except: self.status.text="角度を正しく入力"; return
        if not (0 < open_angle <= 180): self.status.text="角度は0〜180°"; return
        try: width=float(self.width_input.text)
        except: self.status.text="幅(mm)を入力"; return
        cut_angle=open_angle/2.0
        if cut_angle<=0: self.status.text="角度が小さすぎます"; return
        length=width/math.tan(math.radians(cut_angle))
        self.res_angle.text=f"{cut_angle:.1f}°"; self.res_len.text=f"{length:.1f} mm"
        self.status.text="計算完了"

if __name__ == "__main__":
    CameraGuideApp().run()
=======
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
        camera_container = FloatLayout(size_hint_y=0.7)

        # カメラウィジェット
        self.camera_widget = CameraWidget(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )
        camera_container.add_widget(self.camera_widget)

        # 角度ガイドオーバーレイ
        self.angle_overlay = AngleGuideOverlay(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    CameraGuideApp().run()
>>>>>>> Stashed changes
=======
    CameraGuideApp().run()
>>>>>>> Stashed changes
=======
    CameraGuideApp().run()
>>>>>>> Stashed changes
