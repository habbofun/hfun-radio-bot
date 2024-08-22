class EmbedSchema:
    """
    Represents an embed schema for creating rich embeds in Discord messages.

    Args:
        title (str, optional): The title of the embed. Defaults to None.
        description (str, optional): The description of the embed. Defaults to None.
        fields (list, optional): A list of fields in the embed. Defaults to None.
        color (int, optional): The color of the embed. Defaults to 0xb34760.
        thumbnail_url (str, optional): The URL of the thumbnail image. Defaults to None.
        image_url (str, optional): The URL of the main image. Defaults to None.
        footer_text (str, optional): The text in the footer of the embed. Defaults to None.
        author_url (str, optional): The URL of the author's profile. Defaults to None.
    """

    def __init__(self, title: str = None, description: str = None, fields: list = None, color: int = 0xb34760, thumbnail_url: str = None, image_url: str = None, footer_text: str = None, author_url: str = None) -> None:
        self.title = title
        self.description = description
        self.fields = fields
        self.color = color
        self.image_url = image_url
        self.thumbnail_url = thumbnail_url
        self.footer_text = footer_text
        self.author_url = author_url

    def __repr__(self) -> str:
        return f"<EmbedSchema title={self.title} description={self.description} fields={self.fields} color={self.color}> thumbnail_url={self.thumbnail_url} image_url={self.image_url} footer_text={self.footer_text}"

    def get_schema(self) -> dict:
        """
        Returns the embed schema as a dictionary.

        Returns:
            dict: The embed schema.
        """
        schema = {
            "title": self.title,
            "description": self.description,
            "fields": self.fields,
            "color": self.color,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "footer_text": self.footer_text,
            "author_url": self.author_url,
        }
        return schema
