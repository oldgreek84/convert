DOCSTRING = """
command needs:
-path - full/path/to/file
-name - file_name in current directory
-t - [target] - string of file format(default "mobi")
-cat - [category] - category of formatting file (default "ebook")
"""


class InterfaceError(Exception):
    pass
