#!/usr/bin/env python3

import kivy
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
from kivymd.app import MDApp
from kivymd.uix.label import MDIcon

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

        icon_label = MDIcon(
            icon=icon,
            size_hint_x=None,
            width=32,
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


class RaspyTubeApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.youtube_api = YouTubeAPI()
        self.video_player = VideoPlayer()
        self.video_history = []
        self.current_view = "home"
        self.nav_buttons = {}
        self.videos_per_page = 12
        self.current_page = 1
        self.all_videos = []

    def build(self):
        Window.maximize()
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
            size_hint_x=None,
            width=40,
            background_color=(0, 0, 0, 0),
            color=(0.067, 0.067, 0.067, 1),
            font_size="18sp",
        )
        menu_icon = MDIcon(
            icon="menu",
            font_size="18sp",
        )
        menu_button.add_widget(menu_icon)

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
            orientation="horizontal", size_hint_x=None, width=400, spacing=0
        )
        self.search_bar = SearchBar()
        self.search_bar.bind(on_search=self.on_search)
        search_container.add_widget(self.search_bar)

        # Add spacers to center the search bar like pagination
        left_search_spacer = Label(text="")
        right_search_spacer = Label(text="")

        header_layout.add_widget(logo_layout)
        header_layout.add_widget(left_search_spacer)
        header_layout.add_widget(search_container)
        header_layout.add_widget(right_search_spacer)

        content_layout = BoxLayout(orientation="horizontal", spacing=0)

        sidebar = BoxLayout(
            orientation="vertical", size_hint_x=None, width=240, padding=[0, 12, 0, 0]
        )
        sidebar.canvas.before.clear()
        with sidebar.canvas.before:
            Color(0.97, 0.97, 0.97, 1)
            Rectangle(pos=sidebar.pos, size=sidebar.size)

        sidebar_items = [
            ("home", "Home"),
            ("trending-up", "Trending"),
            ("history", "History"),
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

        # Pagination controls
        self.pagination_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=50,
            spacing=10,
            padding=[0, 10, 0, 10],
        )

        self.prev_button = Button(
            text="Previous",
            size_hint_x=None,
            width=100,
            background_color=(0.2, 0.4, 0.8, 1),
            color=(1, 1, 1, 1),
        )
        self.prev_button.bind(on_press=self.prev_page)

        self.page_label = Label(
            text=f"Page {self.current_page}",
            color=(0.067, 0.067, 0.067, 1),
            font_size="16sp",
        )

        self.next_button = Button(
            text="Next",
            size_hint_x=None,
            width=100,
            background_color=(0.2, 0.4, 0.8, 1),
            color=(1, 1, 1, 1),
        )
        self.next_button.bind(on_press=self.next_page)

        # Add spacers to center the pagination controls
        left_spacer = Label(text="")
        right_spacer = Label(text="")

        self.pagination_layout.add_widget(left_spacer)
        self.pagination_layout.add_widget(self.prev_button)
        self.pagination_layout.add_widget(self.page_label)
        self.pagination_layout.add_widget(self.next_button)
        self.pagination_layout.add_widget(right_spacer)

        main_content.add_widget(scroll_view)
        main_content.add_widget(self.pagination_layout)

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
            self.current_page = 1  # Reset to first page
            videos = self.youtube_api.search_videos(query)
            self.display_videos(videos)
        except Exception as e:
            Logger.error(f"Search error: {e}")
            self.show_error("Search failed. Please check your internet connection.")

    def load_trending_videos(self, dt):
        try:
            self.current_page = 1  # Reset to first page
            videos = self.youtube_api.get_trending_videos()
            self.display_videos(videos)
        except Exception as e:
            Logger.error(f"Trending videos error: {e}")
            self.show_error("Failed to load trending videos.")

    def display_videos(self, videos):
        self.all_videos = videos
        self.update_video_display()

    def update_video_display(self):
        self.video_grid.clear_widgets()

        start_index = (self.current_page - 1) * self.videos_per_page
        end_index = start_index + self.videos_per_page
        page_videos = self.all_videos[start_index:end_index]

        for video in page_videos:
            video_card = VideoCard(video)
            video_card.bind(on_video_select=self.play_video)
            self.video_grid.add_widget(video_card)

        self.update_pagination_controls()

    def update_pagination_controls(self):
        total_pages = (
            (len(self.all_videos) - 1) // self.videos_per_page + 1
            if self.all_videos
            else 1
        )
        self.page_label.text = f"Page {self.current_page} of {total_pages}"
        self.prev_button.disabled = self.current_page <= 1
        self.next_button.disabled = self.current_page >= total_pages

    def prev_page(self, instance):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_video_display()

    def next_page(self, instance):
        total_pages = (
            (len(self.all_videos) - 1) // self.videos_per_page + 1
            if self.all_videos
            else 1
        )
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_video_display()

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
            self.current_page = 1  # Reset to first page
            videos = self.youtube_api.get_trending_videos()
            self.display_videos(videos)
        except Exception as e:
            Logger.error(f"Home videos error: {e}")
            self.show_error("Failed to load home videos.")

    def load_history_videos(self):
        self.current_page = 1  # Reset to first page
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
