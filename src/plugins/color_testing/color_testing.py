from plugins.base_plugin.base_plugin import BasePlugin
import logging

logger = logging.getLogger(__name__)

class ColorTesting(BasePlugin):
    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()

        image = self.render_image(dimensions, "color_testing.html", "color_testing.css")

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
        return image
