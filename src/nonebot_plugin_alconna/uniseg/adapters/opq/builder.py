from typing import TYPE_CHECKING
from nonebot.adapters import Bot, Event
from nonebot.adapters.opqbot.event import MessageEvent
from nonebot.adapters.opqbot.bot import Bot
from nonebot.adapters.opqbot.message import MessageSegment, Message

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import (
    At, File, AtAll, Emoji, Hyper, Image, Reply, Video, Voice, Reference
)


class OpqMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.opq


    @build("at")
    def at(self, seg: MessageSegment):
        target = seg.data.get("qq") or seg.data.get("uin")
        return At(target=str(target))

    @build("atall")
    def atall(self, seg: MessageSegment):
        return AtAll()

    @build("image")
    def image(self, seg: MessageSegment):
        return Image(
            url=seg.data.get("url"),  # OPQ 图片段使用 url
            id=seg.data.get("FileMd5") or seg.data.get("FileId"),  # 可用 md5 或 fileId
            width=seg.data.get("Width"),
            height=seg.data.get("Height")
        )

    @build("file")
    def file(self, seg: MessageSegment):
        return File(
            id=seg.data.get("FileId"),
            name=seg.data.get("FileName") or "file.bin",
            url=seg.data.get("Url")
        )

    @build("video")
    def video(self, seg: MessageSegment):
        return Video(
            url=seg.data.get("Url"),
            id=seg.data.get("FileId"),
            duration=seg.data.get("Duration", 0)
        )

    @build("voice")
    def voice(self, seg: MessageSegment):
        return Voice(
            url=seg.data.get("Url"),
            id=seg.data.get("FileId"),
            duration=seg.data.get("Duration", 0)
        )

    @build("reply")
    def reply(self, seg: MessageSegment):
        return Reply(
            id=seg.data.get("MsgSeq"),
            message=seg.data.get("Content", "")
        )

    async def extract_reply(self, event: Event, bot: Bot):
        # OPQ没原生Reply，这里可以先return None，或做自定义逻辑
        return None
