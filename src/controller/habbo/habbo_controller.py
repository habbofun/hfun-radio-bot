import os, httpx
from io import BytesIO
from loguru import logger
from src.helper.singleton import Singleton
from PIL import Image, ImageDraw, ImageFont

@Singleton
class HabboController:
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.client = httpx.AsyncClient(timeout=None)
        self._initialized = True

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._output_dir = os.path.abspath(os.path.join(base_dir, "../../controller/habbo/temp"))
        self._pixel_font_path = os.path.abspath(os.path.join(base_dir, "../../assets/Volter.ttf"))
        self._base_background_path = os.path.abspath(os.path.join(base_dir, "../../assets/habbo_consola_small.png"))

    async def get_user_info(self, username):
        url = f"https://origins.habbo.es/api/public/users?name={username}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def get_avatar_image(self, figure_string):
        url = f"https://www.habbo.es/habbo-imaging/avatarimage?&figure={figure_string}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logger.error(f"Failed to get avatar image: {e}")
            return None

    async def wrap_text(self, text, font, max_width):
        try:
            lines = []
            words = text.split()
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.getlength(test_line) <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            return lines
        except Exception as e:
            logger.error(f"Failed to wrap text: {e}")
            return ["Error wrapping text"]

    async def draw_text_with_border(self, draw, x, y, text, font, text_color, border_color):
        for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, 0)]:
            draw.text((x + offset[0], y + offset[1]), text, font=font, fill=border_color)
        draw.text((x, y), text, font=font, fill=text_color)

    async def create_habbo_image(self, username):
        user_info = await self.get_user_info(username)
        if not user_info:
            return

        if 'error' in user_info:
            logger.error(f"User not found: {username}")
            return None

        avatar_image = await self.get_avatar_image(user_info['figureString'])
        if not avatar_image:
            return

        if not os.path.exists(self._base_background_path):
            logger.error(f"Background image not found: {self._base_background_path}")
            return None

        background = Image.open(self._base_background_path).convert("RGBA")
        avatar_image = avatar_image.convert("RGBA")

        font_path = self._pixel_font_path
        if not os.path.exists(font_path):
            font = ImageFont.load_default()
        else:
            font = ImageFont.truetype(font_path, 9)

        avatar_image = avatar_image.resize((64, 110), Image.LANCZOS)
        
        temp_image = Image.new("RGBA", background.size)
        temp_image.paste(avatar_image, (25, 65), avatar_image)
        combined_image = Image.alpha_composite(background, temp_image)

        draw = ImageDraw.Draw(combined_image)
        text_color = (255, 255, 255)
        border_color = (0, 0, 0)
        online_color = (0, 255, 0)
        offline_color = (255, 0, 0)
        
        last_access = user_info['lastAccessTime']
        member_since = user_info['memberSince']

        last_access_formatted = last_access[8:10] + '-' + last_access[5:7] + '-' + last_access[:4]
        member_since_formatted = member_since[8:10] + '-' + member_since[5:7] + '-' + member_since[:4]

        y_offset = 50
        max_width = 100

        lines = await self.wrap_text(f"Nombre: {user_info['name']}", font, max_width)
        for line in lines:
            await self.draw_text_with_border(draw, 100, y_offset, line, font, text_color, border_color)
            y_offset += 10

        y_offset += 10

        lines = await self.wrap_text(f"Estado: {user_info['motto']}", font, max_width)
        for line in lines:
            await self.draw_text_with_border(draw, 100, y_offset, line, font, text_color, border_color)
            y_offset += 10

        y_offset += 10

        await self.draw_text_with_border(draw, 100, y_offset, "Online: ", font, text_color, border_color)
        await self.draw_text_with_border(draw, 150, y_offset, f"{'Si' if user_info['online'] else 'No'}", font, online_color if user_info['online'] else offline_color, border_color)
        y_offset += 20

        await self.draw_text_with_border(draw, 100, y_offset, f"Últ. Conex.: {last_access_formatted}", font, text_color, border_color)
        y_offset += 20

        await self.draw_text_with_border(draw, 100, y_offset, f"Registro: {member_since_formatted}", font, text_color, border_color)
        y_offset += 20

        await self.draw_text_with_border(draw, 100, y_offset, "Visible: ", font, text_color, border_color)
        await self.draw_text_with_border(draw, 150, y_offset, f"{'Si' if user_info['profileVisible'] else 'No'}", font, online_color if user_info['profileVisible'] else offline_color, border_color)
        y_offset += 20

        await self.draw_text_with_border(draw, 100, y_offset, f"Nivel: {user_info['currentLevel']}", font, text_color, border_color)
        y_offset += 20

        await self.draw_text_with_border(draw, 100, y_offset, f"Experiencia: {user_info['totalExperience']}", font, text_color, border_color)
        y_offset += 20

        os.makedirs(self._output_dir, exist_ok=True)
        output_file = os.path.join(self._output_dir, f"{username}_habbo_console.png")

        combined_image.save(output_file)
        return output_file

    async def delete_image(self, username: str):
        file_path = os.path.join(self._output_dir, f"{username}_habbo_console.png")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.critical(f"Failed to delete image: {e}")

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=None)
        return self

    async def __aexit__(self, _exc_type, _exc_value, _traceback):
        await self.client.aclose()
