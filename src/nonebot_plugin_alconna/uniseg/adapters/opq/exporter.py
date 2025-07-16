from pathlib import Path
from typing import Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.opqbot.bot import Bot as OpqBot
from nonebot.adapters.opqbot.message import Message, MessageSegment
from nonebot.adapters.opqbot.event import MessageEvent

from nonebot.log import logger
from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import (
    Target, SupportAdapter, MessageExporter, SerializeFailed, export
)
from nonebot_plugin_alconna.uniseg.segment import (
    Text, At, Image, File, Audio, AtAll, Reply
)


class OpqMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.opq

    def get_target(self, event: MessageEvent, bot: Union[Bot, None] = None) -> Target:
        if (group_id := getattr(event, "group_id", None)) is not None:
            return Target(
                str(group_id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.opq,
            )
        if (user_id := getattr(event, "user_id", None)) is not None:
            return Target(
                str(user_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.opq,
            )
        raise NotImplementedError("无法确定消息目标")

    def get_message_id(self, event: MessageEvent) -> str:
        if (message_id := getattr(event, "message_id", None)) is not None:
            return str(message_id)
        raise NotImplementedError("无法获取消息ID")

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment(type="at", data={"uin": int(seg.target)})

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment(type="atall", data={})

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.raw:
            return MessageSegment.image(seg.raw)
        if seg.path:
            return MessageSegment.image(Path(seg.path).resolve())
        if seg.url:
            return MessageSegment.image(seg.url)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def file(self, seg: File, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.path:
            return MessageSegment(
                "$opq:file",
                {
                    "name": seg.name or Path(seg.path).name,
                    "file": Path(seg.path).resolve(),
                },
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        """
        群聊：使用 ReplyTo
        私聊：暂时不支持
        """
        return MessageSegment(
            "$opq:reply",
            {
                "MsgSeq": seg.id.get("seq"),
                "MsgTime": seg.id.get("time"),
                "MsgUid": seg.id.get("uid")
            }
        )

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, OpqBot)

        if isinstance(target, Event):
            _target = self.get_target(target, bot)
        else:
            _target = target

        # 处理文件上传
        if msg := message.include("$opq:file"):
            file_info = msg[0].data
            if not _target.private:
                return await bot.upload_group_file(
                    group_id=int(_target.id),
                    filename=file_info["name"],
                    file=str(file_info["file"]),
                    **kwargs,
                )
            else:
                logger.warning("私聊暂不支持文件上传，将跳过")
                return

        # 处理回复
        reply_seg = message.include("$opq:reply")
        if reply_seg:
            # 提取 Reply 信息
            reply_data = reply_seg[0].data
            kwargs.setdefault("ReplyTo", reply_data)

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)

        # 群聊 or 私聊
        if not _target.private:
            return await bot.send_group_msg(
                group_id=int(_target.id),
                message=message,
                **kwargs
            )
        else:
            return await bot.send_private_msg(
                user_id=int(_target.id),
                message=message,
                **kwargs
            )
