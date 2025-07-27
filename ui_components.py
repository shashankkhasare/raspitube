from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
import textwrap

class SearchBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(5)
        
        self.search_input = TextInput(
            hint_text='Search videos...',
            multiline=False,
            size_hint_x=0.8,
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )
        self.search_input.bind(on_text_validate=self.on_enter)
        
        search_button = Button(
            text='Search',
            size_hint_x=0.2,
            background_color=(1, 0, 0, 1),
            color=(1, 1, 1, 1)
        )
        search_button.bind(on_press=self.on_search_press)
        
        self.add_widget(self.search_input)
        self.add_widget(search_button)
    
    def on_enter(self, instance):
        self.dispatch('on_search', self.search_input.text)
    
    def on_search_press(self, instance):
        self.dispatch('on_search', self.search_input.text)
    
    def on_search(self, query):
        pass

class VideoCard(ButtonBehavior, BoxLayout):
    def __init__(self, video_data, **kwargs):
        super().__init__(**kwargs)
        self.video_data = video_data
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(250)
        self.spacing = dp(5)
        self.padding = dp(5)
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.bind(on_press=self.on_video_press)
        
        thumbnail_url = video_data.get('thumbnail_url', '')
        self.thumbnail = AsyncImage(
            source=thumbnail_url,
            size_hint_y=0.7,
            allow_stretch=True,
            keep_ratio=True
        )
        
        title = video_data.get('title', 'No title')
        wrapped_title = '\n'.join(textwrap.wrap(title, width=30))
        
        self.title_label = Label(
            text=wrapped_title,
            size_hint_y=0.2,
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        
        channel_name = video_data.get('channel_name', 'Unknown')
        view_count = video_data.get('view_count', '0')
        
        self.info_label = Label(
            text=f"{channel_name}\n{view_count} views",
            size_hint_y=0.1,
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.7, 0.7, 0.7, 1),
            font_size='10sp'
        )
        
        self.add_widget(self.thumbnail)
        self.add_widget(self.title_label)
        self.add_widget(self.info_label)
    
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def on_video_press(self):
        self.dispatch('on_video_select', self.video_data)
    
    def on_video_select(self, video_data):
        pass

class PlayerControls(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(10)
        self.padding = [dp(10), dp(5)]
        
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 0.9)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        self.play_pause_btn = Button(
            text='⏸️',
            size_hint_x=None,
            width=dp(60),
            background_color=(0.3, 0.3, 0.3, 1),
            font_size='20sp'
        )
        self.play_pause_btn.bind(on_press=self.toggle_play_pause)
        
        self.volume_btn = Button(
            text='🔊',
            size_hint_x=None,
            width=dp(60),
            background_color=(0.3, 0.3, 0.3, 1),
            font_size='16sp'
        )
        self.volume_btn.bind(on_press=self.toggle_mute)
        
        self.time_label = Label(
            text='00:00 / 00:00',
            size_hint_x=0.3,
            color=(1, 1, 1, 1)
        )
        
        self.fullscreen_btn = Button(
            text='⛶',
            size_hint_x=None,
            width=dp(60),
            background_color=(0.3, 0.3, 0.3, 1),
            font_size='20sp'
        )
        self.fullscreen_btn.bind(on_press=self.toggle_fullscreen)
        
        spacer = Label(text='', size_hint_x=1)
        
        self.add_widget(self.play_pause_btn)
        self.add_widget(self.volume_btn)
        self.add_widget(self.time_label)
        self.add_widget(spacer)
        self.add_widget(self.fullscreen_btn)
        
        self.is_playing = False
        self.is_muted = False
    
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def toggle_play_pause(self, instance):
        self.is_playing = not self.is_playing
        self.play_pause_btn.text = '⏸️' if self.is_playing else '▶️'
        self.dispatch('on_play_pause', self.is_playing)
    
    def toggle_mute(self, instance):
        self.is_muted = not self.is_muted
        self.volume_btn.text = '🔇' if self.is_muted else '🔊'
        self.dispatch('on_mute', self.is_muted)
    
    def toggle_fullscreen(self, instance):
        self.dispatch('on_fullscreen')
    
    def update_time(self, current_time, total_time):
        current_min = int(current_time // 60)
        current_sec = int(current_time % 60)
        total_min = int(total_time // 60)
        total_sec = int(total_time % 60)
        
        self.time_label.text = f"{current_min:02d}:{current_sec:02d} / {total_min:02d}:{total_sec:02d}"
    
    def on_play_pause(self, is_playing):
        pass
    
    def on_mute(self, is_muted):
        pass
    
    def on_fullscreen(self):
        pass