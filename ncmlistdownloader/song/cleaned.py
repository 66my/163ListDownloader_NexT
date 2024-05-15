"""
ncmlistdownloader/song/cleaned.py
Core.Ver.2.0.0.240515a1
Author: CooooldWind_
"""

from ncmlistdownloader.common import *
from ncmlistdownloader.common.encode_sec_key import *
from ncmlistdownloader.common.thread_test import best_thread
from ncmlistdownloader.downloader import *
from ncmlistdownloader.common.global_args import *
from ncmlistdownloader.common.encode_sec_key import *
from ncmlistdownloader.editer import *


class Song:
    """
    Song类
    ----------
    存储歌曲信息, 以及各种函数。
    常用的有如下:
    1. `name` / `album` / `artist`
    2. `downloading_state` / `downloading_value`
    3. `raw_info` / `processed_info` / `url_info`
    参数:
    1. `id`: 歌曲id (其实传入url也行)
    """

    def __init__(self, id: str):
        self.id = id
        if self.id.find("163.com") != -1:
            self.id = url_split(url=self.id)
        self.encode_data = {
            "c": str([{
                "id": str(self.id)
            }]),
            "csrf_token": "",
        }
        self.lyric_encode_data = {
            "csrf_token": "",
            "id": str(str(self.id)),
            "lv": -1,
            "tv": -1,
        }
        self.artist: list[str] = []
        self.raw_info = NeteaseParams(
            url=SONG_INFO_API,
            encode_data=self.encode_data).get_resource()["songs"][0]
        self.title = self.raw_info["name"]
        self.album = self.raw_info["al"]["name"]
        for i in self.raw_info["ar"]:
            self.artist.append(i["name"])
        self.artist_str = artist_turn_str(self.artist)
        self.song_url = SONG_FILE_API + self.id
        self.cover_url = self.raw_info["al"]["picUrl"]

    def __str__(self):
        """
        返回存有歌曲信息的字符串。
        ----------
        无参数。
        如果直接`print`这个类就是调用这个函数了。
        """
        return str(self.processed_info)

    """def get_formated_filename(self, suffix):
        formated = format(
            filename=self.filename_format,
            artist=clean(self.artist_str),
            album=clean(self.album),
            id=clean(self.id),
            title=clean(self.title),
        ) + '.' + suffix
        if formated.rfind("/") != -1:
            formated = formated[:formated.rfind("/") + 1] + clean(
                formated[formated.rfind("/") + 1:])
        else:
            formated = clean(formated)
        formated += "." + suffix
        return formated"""
    """def get_info(self):
        
        获取歌曲信息
        ----------
        无参数。
        
        self.raw_info = NeteaseParams(
            url=SONG_INFO_API,
            encode_data=self.encode_data).get_resource()["songs"][0]
        self.title = self.raw_info["name"]
        self.album = self.raw_info["al"]["name"]
        for i in self.raw_info["ar"]:
            self.artist.append(i["name"])
        self.artist_str = artist_turn_str(self.artist)
        self.processed_info = {
            "album": self.album,
            "title": self.title,
            "artist": self.artist,
            "id": self.id,
        }
        self.url_info.update({
            "album_pic": self.raw_info["al"]["picUrl"],
            "song_file": SONG_FILE_API + self.id,
        })
        self.filename_info = {
            "song": self.get_formated_filename("mp3"),
            "pic": self.get_formated_filename("jpg"),
            "lyric": self.get_formated_filename("lrc"),
        }
        self.is_get = True
        return self.raw_info"""

    def song_download_enhanced(self, level: str, cookies=None):
        """
        用另外一个API的下载函数, 需要导入 `cookies` 发挥最大功效。
        """
        flag = True
        level_key = ["standard", "higher", "exhigh", "lossless"]
        for i in level_key:
            if i == level:
                flag = False
        if flag:
            raise Exception("Error at inputing 'level'.")
        """
        data的数据格式: 
        {
            “ids”:str([id]),
            “level”:“standard”,
            “encodeType”:“aac”,
            “csrf_token”: “”
        }
        其中id表示歌曲的id号, 
        level是音乐品质, 
        标准为standard, 
        较高音质为higher, 
        极高音质exhigh, 
        无损音质关键词为lossless。
        """
        enhance_encode_data = {
            "ids": str([self.id]),
            "level": level,
            "encodeType": "mp3",
            "csrf_token": "",
        }
        if level == "lossless":
            enhance_encode_data["encodeType"] = "aac"
        enhanced_info = NeteaseParams(
            encode_data=enhance_encode_data,
            url=SONG_FILE_API_2).get_resource(cookies=cookies)
        enhanced_url = str(enhanced_info['data'][0]['url'])
        if enhanced_url.rfind("?auth") != -1:
            enhanced_url = enhanced_url[:enhanced_url.rfind("?auth")]
        self.song_url = enhanced_url
        return enhanced_url

    def song_download(self):
        # filename = self.get_formated_filename('mp3')
        filename = self.filename_info["song"]
        file_origin = OriginFile(self.song_url)
        if file_origin.total_size <= 0:
            return -1
        file_origin.single_thread_start(filename=filename)
        return filename

    def cover_download(self):
        filename = self.filename_info["pic"]
        # filename = self.get_formated_filename('jpg')
        file_origin = OriginFile(self.cover_url)
        if file_origin.total_size == -1:
            return -1
        file_origin.auto_start(filename=filename)
        return filename

    def lyric_get(self):
        self.lyric = (NeteaseParams(
            url=LYRIC_API, encode_data=self.lyric_encode_data).get_resource()
                      ["lrc"]["lyric"].replace("\n", "\n"))
        # filename = self.get_formated_filename('lrc')
        filename = self.filename_info["lyric"]
        with open(file=filename, mode="w+", encoding="UTF-8") as file:
            file.write(self.lyric)
        return filename

    def attribute_write(self, filename="No filename"):
        """
        往文件里面写入歌曲信息
        ----------
        参数:
        1. `filename`: 文件名, 字符串, 仅 `mp3/flac` 格式
        """
        filename_ready = self.get_formated_filename("mp3")
        if filename == "No filename":
            if self.filename_info.get("song") == None:
                filename = filename_ready
            else:
                filename = self.filename_info["song"]
        attribute_write(filename=filename, info=self.processed_info)

    def cover_write(self,
                    filename="No filename",
                    cover_filename="No cover_filename"):
        """
        专辑封面写入
        ----------
        参数:
        1. `filename`: 文件名, 字符串, 仅 `mp3/flac` 格式
        2. `cover_filename`: 封面的文件名, 字符串, 仅 `jpg` 格式
        """
        if filename == "No filename":
            filename = self.filename_info["song"]
        if cover_filename == "No cover_filename":
            cover_filename = self.filename_info["pic"]
        cover_write(filename=filename, cover_filename=cover_filename)

    def lyric_write(self,
                    filename="No filename",
                    lyric_filename="No lyric_filename"):
        """
        歌词写入
        ----------
        参数:
        1. `filename`: 文件名, 字符串, 仅 `mp3/flac` 格式
        2. `lyric_filename`: 封面的文件名, 字符串, 仅jpg格式
        提示: 如果留空不会怎么样的, 用 `filename_info` 的数据代替
        """
        if filename == "No filename":
            filename = self.filename_info["song"]
        if lyric_filename == "No lyric_filename":
            lyric_filename = self.filename_info["lyric"]
        lyric_write(filename=filename, lyric_filename=lyric_filename)
