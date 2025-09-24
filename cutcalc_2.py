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
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.utils import platform
from kivy.core.image import Image as CoreImage

import os, math, io, time
from glob import glob

# ====== Optional backends ======
OPENCV = False
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

# ====== Overlay for angle lines ======
class AngleGuideOverlay(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.left_angle=135.0  # 左=90..180
        self.right_angle=45.0  # 右=90..0
        self.length_ratio=0.84
        self.center_bias=-0.18
        self.line_width=1.6
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
        Window.clearcolor=BG
        ensure_android_permissions()

        root=FloatLayout()
        scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,size_hint=(1,1))
        Clock.schedule_once(lambda *_: setattr(scroll,"scroll_y",1),0)

        main=BoxLayout(orientation='vertical',padding=12,spacing=8,size_hint_y=None)
        main.bind(minimum_height=main.setter('height'))

        # タイトル
        tcard=Card(orientation='vertical',padding=10,size_hint_y=None,height=86)
        tcard.add_widget(JLabel(text="U字溝カットガイド",font_size=22,bold=True))
        tcard.add_widget(JLabel(text="Android撮影・画像読込 対応",font_size=11,color=SUBTEXT))
        main.add_widget(tcard)

        # 入力
        icard=Card(orientation='horizontal',padding=8,spacing=10,size_hint_y=None,height=90)
        colL=BoxLayout(orientation='vertical',size_hint_x=.5,spacing=4)
        colL.add_widget(JLabel(text="角度(°)",font_size=12,color=SUBTEXT))
        self.angle_input=TextInput(text="90",input_filter='float',multiline=False)
        style_textinput(self.angle_input)  # ← 直接編集OK
        colL.add_widget(self.angle_input)
        colR=BoxLayout(orientation='vertical',size_hint_x=.5,spacing=4)
        colR.add_widget(JLabel(text="幅(mm)",font_size=12,color=SUBTEXT))
        self.width_input=TextInput(text="520",input_filter='float',multiline=False)
        style_textinput(self.width_input); colR.add_widget(self.width_input)
        icard.add_widget(colL); icard.add_widget(colR); main.add_widget(icard)

        # 計算ボタン（押した時だけ計算）
        btn=Button(text="計算する",size_hint_y=None,height=44,
                   background_normal="",background_down="",background_color=(0,0,0,0),
                   color=TEXT,font_name=FONT_NAME)
        with btn.canvas.before:
            Color(*BTN_BG); btn._rect=RoundedRectangle(radius=[14],pos=btn.pos,size=btn.size)
        btn.bind(pos=lambda *a:setattr(btn._rect,"pos",btn.pos),
                 size=lambda *a:setattr(btn._rect,"size",btn.size),
                 on_press=self.calculate_from_manual)
        main.add_widget(btn)

        # カメラ／画像表示エリア
        cam_card=Card(orientation='vertical',padding=0,size_hint_y=None,height=240)
        cam_area=FloatLayout()
        self.camera_view=CameraWidget(size_hint=(1,1),pos_hint={"x":0,"y":0})
        cam_area.add_widget(self.camera_view)
        self.overlay=AngleGuideOverlay(size_hint=(1,1),pos_hint={"x":0,"y":0})
        cam_area.add_widget(self.overlay)
        cam_card.add_widget(cam_area); main.add_widget(cam_card)

        # PCならOpenCVプレビューON
        if platform != "android":
            self.camera_view.start(0)

        # カメラ/ファイル操作バー
        bar=BoxLayout(orientation='horizontal',size_hint_y=None,height=40,spacing=8,padding=[8,6])
        self.btn_open=Button(text="画像を開く", font_name=FONT_NAME)
        self.btn_shot=Button(text="撮影", font_name=FONT_NAME)
        self.btn_cam=Button(text="プレビュー", font_name=FONT_NAME, disabled=(platform=="android"))
        bar.add_widget(self.btn_open); bar.add_widget(self.btn_shot); bar.add_widget(self.btn_cam)
        main.add_widget(bar)

        self.btn_open.bind(on_press=self.pick_image)
        self.btn_shot.bind(on_press=self.take_picture)
        self.btn_cam.bind(on_press=self.toggle_preview)

        # スライダー（1行：左=左バー／右=右バー）
        s_card=Card(orientation='vertical',padding=8,size_hint_y=None,height=96)
        self.info_label=JLabel(text="左:135.0°  右:45.0°  |  開き角:90.0°  長さ:--- mm",font_size=12,color=SUBTEXT)
        s_card.add_widget(self.info_label)
        row=BoxLayout(orientation='horizontal',size_hint_y=None,height=30,spacing=10)

        left_col=BoxLayout(orientation='horizontal',spacing=6,size_hint_x=.5)
        left_col.add_widget(JLabel(text="左バー",font_size=11,color=SUBTEXT,size_hint_x=None,width=48))
        self.left_slider=Slider(min=0,max=100,value=50,step=1)   # 0..100 → 90..180
        left_col.add_widget(self.left_slider)

        right_col=BoxLayout(orientation='horizontal',spacing=6,size_hint_x=.5)
        right_col.add_widget(JLabel(text="右バー",font_size=11,color=SUBTEXT,size_hint_x=None,width=48))
        self.right_slider=Slider(min=0,max=100,value=50,step=1)  # 0..100 → 90..0
        right_col.add_widget(self.right_slider)

        row.add_widget(left_col); row.add_widget(right_col)
        s_card.add_widget(row); main.add_widget(s_card)

        # 結果
        res=Card(orientation='horizontal',padding=10,spacing=16,size_hint_y=None,height=86)
        colA=BoxLayout(orientation='vertical',spacing=2)
        colA.add_widget(JLabel(text="切断角度",font_size=12,color=SUBTEXT))
        self.res_angle=JLabel(text="--.-°",font_size=20,bold=True,color=ACCENT); colA.add_widget(self.res_angle)
        colB=BoxLayout(orientation='vertical',spacing=2)
        colB.add_widget(JLabel(text="切断長さ",font_size=12,color=SUBTEXT))
        self.res_len=JLabel(text="--- mm",font_size=20,bold=True,color=ACCENT); colB.add_widget(self.res_len)
        res.add_widget(colA); res.add_widget(colB); main.add_widget(res)

        # ステータス
        self.status=JLabel(text="",font_size=10,color=SUBTEXT)
        main.add_widget(self.status)
        main.add_widget(Widget(size_hint_y=None,height=10))

        # イベント
        self.left_slider.bind(value=lambda *_: self._update_overlay_and_info())
        self.right_slider.bind(value=lambda *_: self._update_overlay_and_info())

        self._update_overlay_and_info()
        scroll.add_widget(main); root.add_widget(scroll); return root

    # ====== スライダー→角度マッピング ======
    def _left_angle_from_slider(self):
        # 左: 0..100 → 90..180
        return 90.0 + 0.9 * float(self.left_slider.value)
    def _right_angle_from_slider(self):
        # 右: 0..100 → 90..0
        return 90.0 - 0.9 * float(self.right_slider.value)

    def _update_overlay_and_info(self):
        L = self._left_angle_from_slider()
        R = self._right_angle_from_slider()
        self.overlay.set_angles(L, R)
        open_angle = L - R
        self.angle_input.text = f"{open_angle:.1f}"
        self.info_label.text = f"左:{L:.1f}°  右:{R:.1f}°  |  開き角:{open_angle:.1f}°  長さ:{self._calc_length(open_angle)}"

    # ====== 計算ロジック（ボタン押下で実行） ======
    def _calc_length(self, open_angle):
        try: width=float(self.width_input.text) if self.width_input.text else 520.0
        except: width=520.0
        cut_angle=open_angle/2.0
        if cut_angle<=0: return "--- mm"
        length=width/math.tan(math.radians(cut_angle))
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

    # ====== 画像読込（ファイルチューザー） ======
    def pick_image(self, *_):
        if not PLYER:
            self.status.text="ファイルチューザー未対応（plyer未導入）"; return
        def _got_selection(paths):
            if not paths: 
                self.status.text="選択キャンセル"; return
            path = paths[0]
            try:
                # 画像を表示（プレビューにセット）
                self.camera_view.stop()
                self.camera_view.source = path
                self.camera_view.reload()
                self.status.text=f"読込: {os.path.basename(path)}"
            except Exception as e:
                self.status.text=f"表示失敗: {e}"
        try:
            plyer_filechooser.open_file(filters=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")],
                                        multiple=False, on_selection=_got_selection)
        except Exception as e:
            self.status.text=f"ファイル選択エラー: {e}"

    # ====== 撮影（Androidはカメラインテント、PCはOpenCVの1枚取り） ======
    def take_picture(self, *_):
        ts = time.strftime("%Y%m%d_%H%M%S")
        fname = f"shot_{ts}.jpg"
        save_dir = os.path.join(os.getcwd(), "shots")
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, fname)

        if platform == "android" and PLYER:
            try:
                plyer_camera.take_picture(filename=path, on_complete=lambda p: self._after_shot(p))
                self.status.text="カメラ起動中..."
            except Exception as e:
                self.status.text=f"撮影エラー: {e}"
        else:
            # PC: OpenCVから1枚保存
            if not (OPENCV and self.camera_view.capture):
                self.status.text="撮影不可（プレビュー未起動/OPENCV無）"; return
            ok, frame = self.camera_view.capture.read()
            if not ok:
                self.status.text="フレーム取得失敗"; return
            try:
                cv2.imwrite(path, frame)
                self._after_shot(path)
            except Exception as e:
                self.status.text=f"保存失敗: {e}"

    def _after_shot(self, saved_path):
        if not saved_path or not os.path.exists(saved_path):
            self.status.text="保存失敗/キャンセル"; return
        try:
            self.camera_view.stop()
            self.camera_view.source = saved_path
            self.camera_view.reload()
            self.status.text=f"保存: {os.path.basename(saved_path)}"
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
