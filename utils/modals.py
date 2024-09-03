from disnake import TextInputStyle
from disnake.ui import Modal, TextInput


class FeedbackModal(Modal):
    def __init__(self):
        components = [
            TextInput(
                label="Quick title",
                custom_id="title",
                placeholder="tl;dr of your feedback",
                style=TextInputStyle.short,
                max_length=100,
            ),
            TextInput(
                label="Description",
                custom_id="description",
                placeholder="Your feedback goes here",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Provide feedback",
            components=components,
            custom_id="feedback",
            timeout=6000,
        )
