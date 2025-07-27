# RaspyTube

A desktop YouTube application for Raspberry Pi with a YouTube.com-like interface.

## Features

- YouTube-like user interface with video grid layout
- Search videos using YouTube Data API
- Watch trending videos
- Video playback using VLC or MPV
- High-quality video streaming with yt-dlp
- Thumbnail caching and metadata display
- Touch-friendly controls optimized for Raspberry Pi

## Requirements

### System Dependencies

**For Raspberry Pi OS:**
```bash
sudo apt update
sudo apt install python3-pip vlc mpv ffmpeg
```

**For Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-pip vlc mpv ffmpeg python3-dev libgl1-mesa-dev
```

### Python Dependencies

```bash
pip3 install -r requirements.txt
```

## Setup

1. **Clone or download this repository:**
   ```bash
   git clone <repository-url>
   cd raspytube
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Get YouTube Data API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create credentials (API key)
   - Restrict the API key to YouTube Data API v3

4. **Configure the application:**
   ```bash
   cp config.json.template config.json
   ```
   Edit `config.json` and add your YouTube API key:
   ```json
   {
       "youtube_api_key": "YOUR_ACTUAL_API_KEY_HERE"
   }
   ```

5. **Run the application:**
   ```bash
   python3 main.py
   ```

## Configuration Options

Edit `config.json` to customize the application:

- `youtube_api_key`: Your YouTube Data API key (required)
- `preferred_player`: "vlc" or "mpv" (default: "vlc")
- `video_quality`: Maximum video quality (default: "720p")
- `cache_thumbnails`: Enable thumbnail caching (default: true)
- `safe_search`: YouTube safe search setting (default: "moderate")
- `default_region`: Default region for trending videos (default: "US")
- `ui_theme`: UI theme (default: "dark")
- `fullscreen_on_play`: Start videos in fullscreen (default: false)
- `auto_play_next`: Auto-play next video (default: false)

## Controls

- **Search**: Type in the search bar and press Enter or click Search
- **Play Video**: Click on any video thumbnail
- **Player Controls**: Use VLC/MPV built-in controls
- **Fullscreen**: F key in VLC, F key in MPV

## Raspberry Pi Optimization

For better performance on Raspberry Pi:

1. **Enable GPU memory split:**
   ```bash
   sudo raspi-config
   # Advanced Options -> Memory Split -> 128
   ```

2. **Install hardware-accelerated VLC:**
   ```bash
   sudo apt install vlc-plugin-access-extra vlc-plugin-video-output
   ```

3. **Use lower video quality** in config.json:
   ```json
   {
       "video_quality": "480p"
   }
   ```

## Troubleshooting

### Video playback issues:
- Ensure VLC or MPV is properly installed
- Check internet connection
- Try switching between VLC and MPV in config.json

### API issues:
- Verify your YouTube API key is correct
- Check if you've exceeded API quota limits
- Ensure YouTube Data API v3 is enabled

### Performance issues:
- Lower video quality in configuration
- Enable GPU acceleration on Raspberry Pi
- Close other applications to free memory

### Dependencies:
- On Raspberry Pi, some packages might need system-level installation
- Use `sudo apt install python3-kivy` if pip installation fails

## Demo Mode

If no API key is configured, the application will run in demo mode with sample videos.

## License

This project is for educational purposes. Respect YouTube's Terms of Service when using this application.