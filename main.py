#!/usr/bin/env python3

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window

from youtube_api import YouTubeAPI
from video_player import VideoPlayer
from ui_components import VideoCard, SearchBar

kivy.require('2.0.0')

class RaspyTubeApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.youtube_api = YouTubeAPI()
        self.video_player = VideoPlayer()
        
    def build(self):
        Window.size = (1024, 600)
        Window.clearcolor = (0.05, 0.05, 0.05, 1)
        
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        
        logo_label = Label(
            text='RaspyTube',
            font_size='24sp',
            color=(1, 0, 0, 1),
            size_hint_x=None,
            width=150,
            bold=True
        )
        
        self.search_bar = SearchBar()
        self.search_bar.bind(on_search=self.on_search)
        
        header_layout.add_widget(logo_label)
        header_layout.add_widget(self.search_bar)
        
        self.video_grid = GridLayout(cols=3, spacing=10, size_hint_y=None)
        self.video_grid.bind(minimum_height=self.video_grid.setter('height'))
        
        scroll_view = ScrollView()
        scroll_view.add_widget(self.video_grid)
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(scroll_view)
        
        Clock.schedule_once(self.load_trending_videos, 1)
        
        return main_layout
    
    def on_search(self, search_bar, query):
        if query.strip():
            self.search_videos(query)
    
    def search_videos(self, query):
        try:
            videos = self.youtube_api.search_videos(query)
            self.display_videos(videos)
        except Exception as e:
            Logger.error(f"Search error: {e}")
            self.show_error("Search failed. Please check your internet connection.")
    
    def load_trending_videos(self, dt):
        try:
            videos = self.youtube_api.get_trending_videos()
            self.display_videos(videos)
        except Exception as e:
            Logger.error(f"Trending videos error: {e}")
            self.show_error("Failed to load trending videos.")
    
    def display_videos(self, videos):
        self.video_grid.clear_widgets()
        
        for video in videos:
            video_card = VideoCard(video)
            video_card.bind(on_video_select=self.play_video)
            self.video_grid.add_widget(video_card)
    
    def play_video(self, video_card, video_data):
        try:
            self.video_player.play_video(video_data['video_id'])
        except Exception as e:
            Logger.error(f"Video playback error: {e}")
            self.show_error("Failed to play video.")
    
    def show_error(self, message):
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()

if __name__ == '__main__':
    RaspyTubeApp().run()