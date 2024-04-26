import os

from flask import Flask

from env import LABEL_STUDIO_HOST

FILE_TYPE_ICON = {
    ".csv": "vscode-icons:file-type-excel2",
    ".mov": "vscode-icons:file-type-video",
    ".mp4": "vscode-icons:file-type-video",
    ".json": "vscode-icons:file-type-json",
    ".txt": "vscode-icons:file-type-text",
    ".cwa": "mdi:axis-arrow",
}


def _file_icon_name(file_name):
    _, ext = os.path.splitext(file_name)
    icon = FILE_TYPE_ICON.get(ext)
    if icon is not None:
        return icon
    return "vscode-icons:default-file"


def _get_labelstudio_url(subpath: str):
    return f"{LABEL_STUDIO_PUBLIC_URL}/{subpath}"


def _get_env(env):
    return os.environ.get(env)


def define_jinja_functions(app: Flask):
    app.jinja_env.globals.update(
        file_icon_name=_file_icon_name,
        label_studio_path=_get_labelstudio_url,
        get_env=_get_env
    )
