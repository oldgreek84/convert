from formats import Format, register_format


@register_format('fb2')
class Fb2Format(Format):
    def __init__(self, name):
        super().__init__('fb2')

    def allowed_formats(self):
        return ['mobi', 'txt']

    def get_option(self):
        return {}

    def get_extension(self):
        return ".fb2"


@register_format('mobi')
class MobiFormat(Format):
    def __init__(self, name):
        super().__init__('mobi')

    def allowed_formats(self):
        return ['fb2', 'txt']

    def get_option(self):
        return {}

    def get_extension(self):
        return ".mobi"
