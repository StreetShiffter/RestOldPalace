from pathlib import Path
from django.conf import settings


def get_vk_video_urls():
    """Читает embed-ссылки ВК из файла vk_video_links.txt"""
    file_path = Path(settings.BASE_DIR) / "vk_video_links.txt"
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Оставляем только непустые строки и убираем пробелы
        urls = [line.strip() for line in lines if line.strip()]
        return urls
    except Exception:
        return []
