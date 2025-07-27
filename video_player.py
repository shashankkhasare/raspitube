import subprocess
import threading
import time
import os
from typing import Optional, Callable
from kivy.logger import Logger
from kivy.clock import Clock
import yt_dlp

class VideoPlayer:
    def __init__(self, preferred_player='vlc'):
        self.preferred_player = preferred_player
        self.current_process = None
        self.is_playing = False
        self.is_fullscreen = False
        self.current_video_id = None
        self.position_callback = None
        self.player_socket = None
        
        self.ydl_opts = {
            'format': 'best[height<=720]/best',
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'audioformat': 'mp3',
            'outtmpl': '%(id)s.%(ext)s',
            'ignoreerrors': True,
        }
    
    def play_video(self, video_id: str, start_time: int = 0):
        if self.current_process:
            self.stop_video()
        
        self.current_video_id = video_id
        
        # Start video URL extraction and player launch in background thread
        def launch_video():
            try:
                video_url = self._get_video_url(video_id)
                if video_url:
                    self._start_player(video_url, start_time)
                else:
                    Logger.error("Failed to get video URL")
            except Exception as e:
                Logger.error(f"Error playing video: {e}")
        
        threading.Thread(target=launch_video, daemon=True).start()
    
    def _get_video_url(self, video_id: str) -> Optional[str]:
        try:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                formats = info.get('formats', [])
                
                for fmt in formats:
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                        if fmt.get('height', 0) <= 720:
                            return fmt['url']
                
                if formats:
                    return formats[0]['url']
                
                return info.get('url')
        
        except Exception as e:
            Logger.error(f"yt-dlp error: {e}")
            return None
    
    def _start_player(self, video_url: str, start_time: int = 0):
        try:
            if self.preferred_player == 'vlc':
                self._start_vlc(video_url, start_time)
            elif self.preferred_player == 'mpv':
                self._start_mpv(video_url, start_time)
            else:
                Logger.error(f"Unknown player: {self.preferred_player}")
        except Exception as e:
            Logger.error(f"Error starting player: {e}")
    
    def _start_vlc(self, video_url: str, start_time: int = 0):
        vlc_cmd = [
            'vlc',
            video_url,
            '--extraintf', 'http',
            '--http-password', 'raspytube',
            '--http-port', '8080',
            '--fullscreen' if self.is_fullscreen else '--no-fullscreen',
            '--no-video-title-show',
            '--quiet',
            '--network-caching=300',
            '--file-caching=300',
            '--live-caching=300',
            '--sout-mux-caching=300',
            '--cr-average=40',
            '--drop-late-frames',
            '--skip-frames'
        ]
        
        if start_time > 0:
            vlc_cmd.extend(['--start-time', str(start_time)])
        
        try:
            self.current_process = subprocess.Popen(
                vlc_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.is_playing = True
            Logger.info("VLC player started")
            
            self._start_position_monitor()
            
        except FileNotFoundError:
            Logger.error("VLC not found. Please install VLC media player.")
            self._try_fallback_player(video_url, start_time)
        except Exception as e:
            Logger.error(f"VLC error: {e}")
            self._try_fallback_player(video_url, start_time)
    
    def _start_mpv(self, video_url: str, start_time: int = 0):
        mpv_cmd = [
            'mpv',
            video_url,
            '--input-ipc-server=/tmp/mpv-socket',
            '--fullscreen' if self.is_fullscreen else '--no-fullscreen',
            '--no-terminal',
            '--quiet'
        ]
        
        if start_time > 0:
            mpv_cmd.extend(['--start', f'+{start_time}'])
        
        try:
            self.current_process = subprocess.Popen(
                mpv_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.is_playing = True
            Logger.info("MPV player started")
            
            self._start_position_monitor()
            
        except FileNotFoundError:
            Logger.error("MPV not found. Please install MPV media player.")
            self._try_fallback_player(video_url, start_time)
        except Exception as e:
            Logger.error(f"MPV error: {e}")
            self._try_fallback_player(video_url, start_time)
    
    def _try_fallback_player(self, video_url: str, start_time: int = 0):
        fallback_player = 'mpv' if self.preferred_player == 'vlc' else 'vlc'
        Logger.info(f"Trying fallback player: {fallback_player}")
        
        original_player = self.preferred_player
        self.preferred_player = fallback_player
        
        try:
            self._start_player(video_url, start_time)
        except Exception as e:
            Logger.error(f"Fallback player also failed: {e}")
            self.preferred_player = original_player
    
    def _start_position_monitor(self):
        if self.position_callback:
            def monitor():
                while self.current_process and self.current_process.poll() is None:
                    try:
                        if self.preferred_player == 'vlc':
                            position_info = self._get_vlc_position()
                        else:
                            position_info = self._get_mpv_position()
                        
                        if position_info:
                            Clock.schedule_once(
                                lambda dt: self.position_callback(position_info), 0
                            )
                    except Exception as e:
                        Logger.debug(f"Position monitor error: {e}")
                    
                    time.sleep(1)
            
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
    
    def _get_vlc_position(self):
        try:
            import requests
            response = requests.get(
                'http://localhost:8080/requests/status.xml',
                auth=('', 'raspytube'),
                timeout=1
            )
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                time_elem = root.find('.//time')
                length_elem = root.find('.//length')
                
                if time_elem is not None and length_elem is not None:
                    current_time = int(time_elem.text)
                    total_time = int(length_elem.text)
                    return {'current': current_time, 'total': total_time}
        except Exception:
            pass
        return None
    
    def _get_mpv_position(self):
        return None
    
    def pause_video(self):
        if self.current_process:
            try:
                if self.preferred_player == 'vlc':
                    import requests
                    requests.get(
                        'http://localhost:8080/requests/status.xml?command=pl_pause',
                        auth=('', 'raspytube'),
                        timeout=1
                    )
                elif self.preferred_player == 'mpv':
                    pass
                
                self.is_playing = False
            except Exception as e:
                Logger.error(f"Pause error: {e}")
    
    def resume_video(self):
        if self.current_process:
            try:
                if self.preferred_player == 'vlc':
                    import requests
                    requests.get(
                        'http://localhost:8080/requests/status.xml?command=pl_play',
                        auth=('', 'raspytube'),
                        timeout=1
                    )
                elif self.preferred_player == 'mpv':
                    pass
                
                self.is_playing = True
            except Exception as e:
                Logger.error(f"Resume error: {e}")
    
    def stop_video(self):
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            except Exception as e:
                Logger.error(f"Stop error: {e}")
            finally:
                self.current_process = None
                self.is_playing = False
                self.current_video_id = None
    
    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        
        if self.current_process:
            try:
                if self.preferred_player == 'vlc':
                    import requests
                    requests.get(
                        'http://localhost:8080/requests/status.xml?command=fullscreen',
                        auth=('', 'raspytube'),
                        timeout=1
                    )
            except Exception as e:
                Logger.error(f"Fullscreen toggle error: {e}")
    
    def set_volume(self, volume: int):
        if self.current_process and 0 <= volume <= 100:
            try:
                if self.preferred_player == 'vlc':
                    import requests
                    requests.get(
                        f'http://localhost:8080/requests/status.xml?command=volume&val={volume}',
                        auth=('', 'raspytube'),
                        timeout=1
                    )
            except Exception as e:
                Logger.error(f"Volume error: {e}")
    
    def seek_to(self, position: int):
        if self.current_process:
            try:
                if self.preferred_player == 'vlc':
                    import requests
                    requests.get(
                        f'http://localhost:8080/requests/status.xml?command=seek&val={position}',
                        auth=('', 'raspytube'),
                        timeout=1
                    )
            except Exception as e:
                Logger.error(f"Seek error: {e}")
    
    def set_position_callback(self, callback: Callable):
        self.position_callback = callback
    
    def cleanup(self):
        self.stop_video()