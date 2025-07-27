#!/usr/bin/env python3

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from ui_components import SearchBar, VideoCard
from video_player import VideoPlayer
from youtube_api import YouTubeAPI

kivy.require("2.0.0")


class NavItem(ButtonBehavior, BoxLayout):
    def __init__(self, icon, text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 48
        self.padding = [20, 8, 16, 8]
        self.spacing = 12

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle

            Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)

        icon_label = Label(
            text=icon,
            size_hint_x=None,
            width=32,
            color=(0.067, 0.067, 0.067, 1),
            font_size="18sp",
        )
        text_label = Label(
            text=text,
            halign="left",
            valign="center",
            color=(0.067, 0.067, 0.067, 1),
            font_size="15sp",
        )
        text_label.bind(size=text_label.setter("text_size"))

        self.add_widget(icon_label)
        self.add_widget(text_label)

    def update_bg(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, active):
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle

            if active:
                Color(0.9, 0.9, 0.9, 1)
            else:
                Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)


class RaspyTubeApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.youtube_api = YouTubeAPI()
        self.video_player = VideoPlayer()
        self.video_history = []
        self.current_view = "home"
        self.nav_buttons = {}

    def build(self):
        Window.size = (1024, 600)
        Window.clearcolor = (1, 1, 1, 1)

        main_layout = BoxLayout(orientation="vertical", spacing=0, padding=0)

        header_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=56,
            padding=[16, 0, 16, 0],
        )
        header_layout.canvas.before.clear()
        with header_layout.canvas.before:
            from kivy.graphics import Color, Rectangle

            Color(1, 1, 1, 1)
            Rectangle(pos=header_layout.pos, size=header_layout.size)

        logo_layout = BoxLayout(
            orientation="horizontal", size_hint_x=None, width=150, spacing=8
        )

        menu_button = Button(
            text="☰",
            size_hint_x=None,
            width=40,
            background_color=(0, 0, 0, 0),
            color=(0.067, 0.067, 0.067, 1),
            font_size="18sp",
        )

        logo_label = Label(
            text="RaspyTube",
            font_size="20sp",
            color=(0.067, 0.067, 0.067, 1),
            size_hint_x=None,
            width=100,
            bold=True,
        )

        logo_layout.add_widget(menu_button)
        logo_layout.add_widget(logo_label)

        search_container = BoxLayout(
            orientation="horizontal", size_hint_x=0.4, spacing=0
        )
        self.search_bar = SearchBar()
        self.search_bar.bind(on_search=self.on_search)
        search_container.add_widget(self.search_bar)

        right_icons = BoxLayout(
            orientation="horizontal", size_hint_x=None, width=120, spacing=8
        )

        create_button = Button(
            text="📹",
            size_hint_x=None,
            width=40,
            background_color=(0, 0, 0, 0),
            color=(0.067, 0.067, 0.067, 1),
            font_size="16sp",
        )

        notifications_button = Button(
            text="🔔",
            size_hint_x=None,
            width=40,
            background_color=(0, 0, 0, 0),
            color=(0.067, 0.067, 0.067, 1),
            font_size="16sp",
        )

        profile_button = Button(
            text="👤",
            size_hint_x=None,
            width=32,
            background_color=(0.2, 0.4, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size="16sp",
        )

        right_icons.add_widget(create_button)
        right_icons.add_widget(notifications_button)
        right_icons.add_widget(profile_button)

        header_layout.add_widget(logo_layout)
        header_layout.add_widget(Label(text="", size_hint_x=0.3))
        header_layout.add_widget(search_container)
        header_layout.add_widget(Label(text="", size_hint_x=0.3))
        header_layout.add_widget(right_icons)

        content_layout = BoxLayout(orientation="horizontal", spacing=0)

        sidebar = BoxLayout(
            orientation="vertical", size_hint_x=None, width=240, padding=[0, 12, 0, 0]
        )
        sidebar.canvas.before.clear()
        with sidebar.canvas.before:
            Color(0.97, 0.97, 0.97, 1)
            Rectangle(pos=sidebar.pos, size=sidebar.size)

        sidebar_items = [
            ("🏠", "Home"),
            ("🔥", "Trending"),
            ("📜", "History"),
        ]

        for icon, text in sidebar_items:
            nav_item = NavItem(icon, text)
            nav_item.bind(
                on_press=lambda x, nav_type=text.lower(): self.on_nav_click(nav_type)
            )

            self.nav_buttons[text.lower()] = nav_item
            if text.lower() == "home":
                nav_item.set_active(True)

            sidebar.add_widget(nav_item)

        main_content = BoxLayout(orientation="vertical", padding=[24, 12, 24, 0])

        self.video_grid = GridLayout(
            cols=4, spacing=16, size_hint_y=None, padding=[0, 0, 0, 24]
        )
        self.video_grid.bind(minimum_height=self.video_grid.setter("height"))

        scroll_view = ScrollView()
        scroll_view.add_widget(self.video_grid)

        main_content.add_widget(scroll_view)

        content_layout.add_widget(sidebar)
        content_layout.add_widget(main_content)

        main_layout.add_widget(header_layout)
        main_layout.add_widget(content_layout)

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
            self.video_history.append(video_data)
            self.video_player.play_video(video_data["video_id"])
        except Exception as e:
            Logger.error(f"Video playback error: {e}")
            self.show_error("Failed to play video.")

    def on_nav_click(self, nav_type):
        self.current_view = nav_type
        Logger.info(f"Navigation clicked: {nav_type}")

        for name, nav_item in self.nav_buttons.items():
            nav_item.set_active(name == nav_type)

        if nav_type == "home":
            self.load_home_videos()
        elif nav_type == "trending":
            self.load_trending_videos(None)
        elif nav_type == "history":
            self.load_history_videos()

    def load_home_videos(self):
        try:
            videos = self.youtube_api.get_trending_videos()
            self.display_videos(videos)
        except Exception as e:
            Logger.error(f"Home videos error: {e}")
            self.show_error("Failed to load home videos.")

    def load_history_videos(self):
        if not self.video_history:
            self.video_grid.clear_widgets()
            no_history_label = Label(
                text="No videos in history yet.\nWatch some videos to see them here!",
                color=(0.4, 0.4, 0.4, 1),
                font_size="16sp",
                halign="center",
            )
            self.video_grid.add_widget(no_history_label)
        else:
            recent_history = list(reversed(self.video_history[-20:]))
            self.display_videos(recent_history)

    def show_error(self, message):
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()


if __name__ == "__main__":
    RaspyTubeApp().run()
