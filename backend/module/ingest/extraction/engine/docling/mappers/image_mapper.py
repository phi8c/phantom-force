from ..models.image import (
    ImageBlock
)


class ImageMapper:

    @staticmethod
    def map_image(
        image,
        image_id: int,
    ):

        caption = None

        try:
            caption = image.caption_text
        except Exception:
            pass

        return ImageBlock(
            id=f"image_{image_id}",
            caption=caption,
        )