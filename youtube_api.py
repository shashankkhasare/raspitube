import json
from typing import Dict, List, Optional

import requests
from kivy.logger import Logger


class YouTubeAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key_from_config()
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def _get_api_key_from_config(self) -> Optional[str]:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("youtube_api_key")
        except FileNotFoundError:
            Logger.warning(
                "config.json not found. Please create it with your YouTube API key."
            )
            return None
        except Exception as e:
            Logger.error(f"Error reading config: {e}")
            return None

    def search_videos(self, query: str, max_results: int = 20) -> List[Dict]:
        if not self.api_key:
            Logger.error("YouTube API key not configured")
            return self._get_demo_videos()

        try:
            url = f"{self.base_url}/search"
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "key": self.api_key,
                "order": "relevance",
                "safeSearch": "moderate",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            videos = []

            for item in data.get("items", []):
                try:
                    if isinstance(item, dict):
                        video = self._parse_video_item(item)
                        if video:
                            videos.append(video)
                    else:
                        Logger.warning(f"Unexpected item type: {type(item)} - {item}")
                except Exception as e:
                    Logger.error(f"Error parsing video item: {e} - Item: {item}")
                    continue

            return videos

        except requests.RequestException as e:
            Logger.error(f"API request failed: {e}")
            return self._get_demo_videos()
        except Exception as e:
            Logger.error(f"Search error: {e}")
            return self._get_demo_videos()

    def get_trending_videos(
        self, region_code: str = "US", max_results: int = 20
    ) -> List[Dict]:
        if not self.api_key:
            Logger.warning("YouTube API key not configured, using demo data")
            return self._get_demo_videos()

        try:
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": max_results,
                "key": self.api_key,
                "videoCategoryId": "0",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            videos = []

            for item in data.get("items", []):
                try:
                    if isinstance(item, dict):
                        video = self._parse_video_item(item, include_stats=True)
                        if video:
                            videos.append(video)
                    else:
                        Logger.warning(f"Unexpected item type: {type(item)} - {item}")
                except Exception as e:
                    Logger.error(f"Error parsing video item: {e} - Item: {item}")
                    continue

            return videos

        except requests.RequestException as e:
            Logger.error(f"API request failed: {e}")
            return self._get_demo_videos()
        except Exception as e:
            Logger.error(f"Trending videos error: {e}")
            return self._get_demo_videos()

    def get_video_details(self, video_id: str) -> Optional[Dict]:
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
                "key": self.api_key,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            if items:
                return self._parse_video_item(
                    items[0], include_stats=True, include_details=True
                )

            return None

        except Exception as e:
            Logger.error(f"Video details error: {e}")
            return None

    def _parse_video_item(
        self, item: Dict, include_stats: bool = False, include_details: bool = False
    ) -> Dict:
        if not isinstance(item, dict):
            Logger.error(f"Expected dict but got {type(item)}: {item}")
            return {}

        snippet = item.get("snippet", {})
        if not isinstance(snippet, dict):
            Logger.error(f"Expected snippet dict but got {type(snippet)}: {snippet}")
            return {}

        # Get video_id safely
        video_id = None
        if "id" in item:
            if isinstance(item["id"], dict):
                video_id = item["id"].get("videoId")
            else:
                video_id = item["id"]

        if not video_id:
            Logger.warning(f"No video_id found in item: {item}")
            return {}

        video_data = {
            "video_id": video_id,
            "title": snippet.get("title", "No title"),
            "channel_name": snippet.get("channelTitle", "Unknown Channel"),
            "channel_id": snippet.get("channelId", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail_url": self._get_best_thumbnail(snippet.get("thumbnails", {})),
        }

        if include_stats and "statistics" in item:
            stats = item["statistics"]
            video_data.update(
                {
                    "view_count": self._format_view_count(stats.get("viewCount", "0")),
                    "like_count": stats.get("likeCount", "0"),
                    "comment_count": stats.get("commentCount", "0"),
                }
            )
        else:
            video_data["view_count"] = "N/A views"

        if include_details and "contentDetails" in item:
            details = item["contentDetails"]
            video_data.update(
                {
                    "duration": self._parse_duration(details.get("duration", "PT0S")),
                    "definition": details.get("definition", "sd"),
                }
            )

        return video_data

    def _get_best_thumbnail(self, thumbnails: Dict) -> str:
        for quality in ["maxres", "high", "medium", "default"]:
            if quality in thumbnails:
                return thumbnails[quality]["url"]
        return ""

    def _format_view_count(self, view_count: str) -> str:
        try:
            count = int(view_count)
            if count >= 1000000:
                return f"{count / 1000000:.1f}M views"
            elif count >= 1000:
                return f"{count / 1000:.1f}K views"
            else:
                return f"{count} views"
        except (ValueError, TypeError):
            return "N/A views"

    def _parse_duration(self, duration: str) -> str:
        import re

        pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
        match = re.match(pattern, duration)

        if not match:
            return "0:00"

        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def _get_demo_videos(self) -> List[Dict]:
        return [
            {
                "video_id": "dQw4w9WgXcQ",
                "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
                "channel_name": "Rick Astley",
                "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
                "description": "The official video for Never Gonna Give You Up by Rick Astley",
                "published_at": "2009-10-25T06:57:33Z",
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                "view_count": "1.4B views",
            },
            {
                "video_id": "L_jWHffIx5E",
                "title": "Smash Mouth - All Star (Official Music Video)",
                "channel_name": "Smash Mouth",
                "channel_id": "UCDGYmT0ehEEMt8DqH1sKGCA",
                "description": "Official music video for All Star by Smash Mouth",
                "published_at": "2010-05-26T23:14:58Z",
                "thumbnail_url": "https://i.ytimg.com/vi/L_jWHffIx5E/hqdefault.jpg",
                "view_count": "720M views",
            },
            {
                "video_id": "ZZ5LpwO-An4",
                "title": "HEYYEYAAEYAAAEYAEYAA",
                "channel_name": "ProtoOfSnagem",
                "channel_id": "UCOzQC1E5kWvN7EYe8bYxFDw",
                "description": "He-Man sings",
                "published_at": "2005-12-01T02:42:00Z",
                "thumbnail_url": "https://i.ytimg.com/vi/ZZ5LpwO-An4/hqdefault.jpg",
                "view_count": "97M views",
            },
        ]
