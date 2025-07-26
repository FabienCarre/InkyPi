import os
from utils.app_utils import resolve_path, get_font
from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image, ImageColor, ImageDraw, ImageFont
from io import BytesIO
import logging
import numpy as np
import math
from datetime import datetime
import pytz
import requests
import re

logger = logging.getLogger(__name__)

class Divia(BasePlugin):
    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()

        stop_info_drapeau_a = {
            "line_id": "96", # T2 > Valmy
            "stop_code": "1465" # Drapeau
        }

        stop_info_drapeau_r = {
            "line_id": "185", # T2 > Chenôve Centre
            "stop_code": "1497" # Drapeau
        }

        stop_info_marsannay_charon_a = {
            "line_id": "106", # B14 > Charet
            "stop_code": "1246" # Marsannay Charon
        }

        stop_info_marsannay_r = {
            "line_id": "85", # L4 > Monge
            "stop_code": "952" # Marsannay
        }

        stop_info_chenove_centre_a = {
            "line_id": "96", # T2 > Valmy
            "stop_code": "1459" # Chenôve Centre
        }

        horaires_divia = [
            {
                "title": "T2 Chenôve Centre",
                "items": [
                    {
                        "direction": "Valmy",
                        "time": [result["text"] for result in self.get_next_passages(stop_info_chenove_centre_a)]
                    }
                ]
            },
            {
                "title": "L4 Marsannay",
                "items": [
                    {
                        "direction": "Monge",
                        "time": [result["text"] for result in self.get_next_passages(stop_info_marsannay_r)]
                    }
                ]
            },
            {
                "title": "B14 Marsannay Charon",
                "items": [
                    {
                        "direction": "Charet",
                        "time": [result["text"] for result in self.get_next_passages(stop_info_marsannay_charon_a)]
                    }
                ]
            }
        ]

        template_params = {
            "horaires_divia": horaires_divia,
            "plugin_settings": settings
        }

        image = self.render_image(dimensions, "divia.html", "divia.css", template_params)

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
        return image

    def get_next_passages(self, stop_info):

        # You need to provide actual values for line_id and stop_code
        line_id = stop_info.get("line_id")
        stop_code = stop_info.get("stop_code")

        if not line_id or not stop_code:
            logger.error("Missing line_id or stop_code in stop_info")
            return None

        url = 'https://www.divia.fr/bus-tram?type=479'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = f"requete=arret_prochainpassage&requete_val%5Bid_ligne%5D={line_id}&requete_val%5Bid_arret%5D={stop_code}"

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = self.extract_next_passages(response.text)
            return result
        except Exception as e:
            logger.error(f"Error fetching next passage: {e}")
            return None

    def extract_next_passages(self, html):
        result = []
        regex = re.compile(r'<span class="uk-badge">\s*(((0?|[12])\d):(\d{2}))<\/span>', re.IGNORECASE)
        for match in regex.finditer(html):
            time_text = match.group(1)
            hours = int(match.group(3))
            minutes = int(match.group(4))
            now = datetime.now()
            passage_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            # If the time has already passed today, assume it's for the next day
            if passage_time < now:
                passage_time = passage_time.replace(day=now.day + 1)
                result.append({
                    "text": time_text,
                    "date": passage_time
                })
        return result