from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.opq

    def get_builder(self):
        from .builder import OpqMessageBuilder

        return OpqMessageBuilder()

    def get_exporter(self):
        from .exporter import OpqMessageExporter

        return OpqMessageExporter()

    # def get_fetcher(self):
    #     from .target import OpqargetFetcher

    #     return OpqargetFetcher()
