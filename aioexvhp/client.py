# aioeXVHP - Asynchronous Python Interface for Video Hosting Platforms
# Copyright (C) 2021 - eXhumer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from string import ascii_letters, digits
from io import BufferedReader, BytesIO, SEEK_END, SEEK_SET
from mimetypes import guess_type
from pathlib import Path
from random import choice

from boto3 import client
from bs4 import BeautifulSoup
from aiohttp import ClientSession, FormData, StreamReader
from aiohttp.hdrs import USER_AGENT

from . import default_user_agent


def _client_session_setup(
    session: ClientSession | None = None,
    user_agent: str | None = None,
):
    """Method to setup or create a HTTP client session with proper user-agent
    """
    if session is None:
        session = ClientSession()

    if USER_AGENT not in session.headers:
        if user_agent is None:
            session.headers[USER_AGENT] = default_user_agent

        else:
            session.headers[USER_AGENT] = user_agent

    return session


class Imgur:
    api_url = "https://api.imgur.com"
    base_url = "https://imgur.com"
    client_id = "546c25a59c58ad7"

    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ):
        self.__session = _client_session_setup(
            session=session,
            user_agent=user_agent,
        )

    async def generate_album(self):
        return await self.__session.post(
            f"{Imgur.api_url}/3/album",
            params={"client_id": Imgur.client_id},
            json={},
        )

    async def poll_upload_tickets(self, *tickets: str):
        return await self.__session.get(
            f"{Imgur.base_url}/upload/poll",
            params={
                "client_id": Imgur.client_id,
                "tickets[]": tickets,
            },
        )

    async def update_album_metadata(self, deletehash: str, **metadata: str):
        return await self.__session.post(
            f"{Imgur.api_url}/3/album/{deletehash}",
            params={"client_id": Imgur.client_id},
            json=metadata,
        )

    async def update_media_metadata(self, deletehash: str, **metadata: str):
        return await self.__session.post(
            f"{Imgur.api_url}/3/image/{deletehash}",
            params={"client_id": Imgur.client_id},
            json=metadata,
        )

    async def upload_media_from_file(self, media_path: Path):
        return await self.upload_media(
            media_path.open(mode="rb"),
            media_path.name,
        )

    async def upload_media(
        self,
        media_content: BufferedReader | BytesIO | StreamReader,
        media_filename: str,
    ):
        if not media_filename.endswith((".mp4")):
            raise ValueError("Unsupported media type!")

        media_key = (
            "video"
            if media_filename.endswith((".mp4"))
            else "image"
        )
        form_data = FormData()
        form_data.add_field(
            media_key,
            media_content,
            content_type=guess_type(media_filename)[0],
            filename=media_filename,
        )
        form_data.add_field("type", "file")
        form_data.add_field("name", media_filename)

        return await self.__session.post(
            f"{Imgur.api_url}/3/image",
            data=form_data,
            params={"client_id": Imgur.client_id},
        )

    async def delete_album(self, deletehash: str):
        return await self.__session.delete(
            f"{Imgur.api_url}/3/album/{deletehash}",
            params={"client_id": Imgur.client_id},
        )

    async def delete_media(self, deletehash: str):
        return await self.__session.delete(
            f"{Imgur.api_url}/3/image/{deletehash}",
            params={"client_id": Imgur.client_id},
        )

    async def add_media_to_album(
        self,
        album_deletehash: str,
        media_deletehash: str,
    ):
        return await self.__session.post(
            f"{Imgur.api_url}/3/album/{album_deletehash}/add",
            params={"client_id": Imgur.client_id},
            json={"deletehashes": media_deletehash},
        )

    async def arrange_album(
        self,
        album_deletehash: str,
        cover_media_id: str,
        *media_deletehashes: str,
    ):
        return await self.__session.put(
            f"{Imgur.api_url}/3/album/{album_deletehash}",
            params={"client_id": Imgur.client_id},
            json={"cover": cover_media_id, "deletehashes": media_deletehashes},
        )

    async def check_captcha(
        self,
        total_upload: int,
        g_recaptcha_response: str | None = None,
    ):
        return await self.__session.post(
            f"{Imgur.api_url}/3/upload/checkcaptcha",
            params={"client_id": Imgur.client_id},
            json={
                "total_upload": total_upload,
                "g-recaptcha-response": g_recaptcha_response,
            },
        )


class JustStreamLive:
    api_url = "https://api.juststream.live"

    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ):
        self.__session = _client_session_setup(
            session=session,
            user_agent=user_agent,
        )

    async def upload_from_file(self, video_path: Path):
        return await self.upload_video(
            video_path.open(mode="rb"), video_path.name,
        )

    async def upload_video(
        self,
        video_content: BytesIO | BufferedReader | StreamReader,
        video_filename: str,
    ):
        form_data = FormData()
        form_data.add_field(
            "file",
            video_content,
            content_type=guess_type(video_filename)[0],
            filename=video_filename,
        )

        return await self.__session.post(
            f"{JustStreamLive.api_url}/videos/upload",
            data=form_data,
        )

    async def mirror_from_url(self, url: str):
        return await self.__session.post(
            f"{JustStreamLive.api_url}/videos/upload-from-url",
            data={"url": url},
        )

    async def mirror_streamja_video(self, video_id: str):
        return await self.mirror_from_url(f"{Streamja.base_url}/{video_id}")

    async def mirror_streamable_video(self, video_id: str):
        return await self.mirror_from_url(f"{Streamable.base_url}/{video_id}")

    async def mirror_streamwo_video(self, video_id: str):
        return await self.mirror_from_url(f"{Streamwo.base_url}/{video_id}")

    async def mirror_streamff_video(
        self,
        video_id: str,
        mirror_filename: str = "Mirror.mp4",
        streamff_client: Streamff | None = None,
    ):
        if streamff_client is None:
            streamff_client = Streamff(self.__session)

        video_res = await streamff_client.get_video(video_id)

        if not video_res.ok:
            return video_res

        return await self.upload_video(video_res.content, mirror_filename)


class Streamable:
    api_url = "https://ajax.streamable.com"
    base_url = "https://streamable.com"
    frontend_react_version = "03db98af3545197e67cb96893d9e9d8729eee743"

    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ):
        self.__session = _client_session_setup(
            session=session,
            user_agent=user_agent,
        )

    async def me(self):
        return await self.__session.get(f"{Streamable.api_url}/me")

    async def generate_upload_shortcode(self, video_sz: int):
        return await self.__session.get(
            f"{Streamable.api_url}/shortcode",
            params={
                "version": Streamable.frontend_react_version,
                "size": video_sz,
            },
        )

    async def generate_streamable_clip_shortcode(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        return await self.__session.post(
            f"{Streamable.api_url}/videos",
            json={
                "extract_id": video_id,
                "extractor": "streamable",
                "source": f"{Streamable.base_url}/{video_id}",
                "status": 1,
                "title": mirror_title,
                "upload_source": "clip",
            },
        )

    async def generate_streamja_clip_shortcode(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        return await self.__session.post(
            f"{Streamable.api_url}/videos",
            json={
                "extract_id": video_id,
                "extractor": "generic",
                "source": f"{Streamja.base_url}/{video_id}",
                "status": 1,
                "title": mirror_title,
                "upload_source": "clip",
            },
        )

    async def generate_streamwo_clip_shortcode(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        return await self.__session.post(
            f"{Streamable.api_url}/videos",
            json={
                "extract_id": video_id,
                "extractor": "generic",
                "source": f"{Streamwo.base_url}/{video_id}",
                "status": 1,
                "title": mirror_title,
                "upload_source": "clip",
            },
        )

    async def generate_streamff_clip_shortcode(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        return await self.__session.post(
            f"{Streamable.api_url}/videos",
            json={
                "extract_id": video_id,
                "extractor": "generic",
                "source": f"{Streamff.base_url}/v/{video_id}",
                "status": 1,
                "title": mirror_title,
                "upload_source": "clip",
            },
        )

    async def start_transcode_upload(
        self,
        video_shortcode: str,
        video_size: int,
        transcoder_token: str,
    ):
        return await self.__session.post(
            f"{Streamable.api_url}/transcode/{video_shortcode}",
            json={
                "shortcode": video_shortcode,
                "size": video_size,
                "token": transcoder_token,
                "upload_source": "web",
                "url": "https://streamables-upload.s3.amazonaws.com" +
                f"/upload/{video_shortcode}",
            },
        )

    async def update_video_metadata(
        self,
        video_shortcode: str,
        video_filename: str,
        video_size: int,
        video_title: str | None = None,
    ):
        return await self.__session.put(
            f"{Streamable.api_url}/videos/{video_shortcode}",
            json={
                "original_name": video_filename,
                "original_size": video_size,
                "title": (
                    video_title
                    if video_title is not None
                    else Path(video_filename).stem
                ),
                "upload_source": "web",
            },
            params={"purge": ""},
        )

    async def upload_from_file(
        self,
        video_path: Path,
        video_title: str | None = None,
    ):
        return await self.upload_video(
            video_path.open(mode="rb"),
            video_path.name,
            video_title=video_title,
        )

    async def upload_video(
        self,
        video_content: BytesIO | BufferedReader,
        video_filename: str,
        video_title: str | None = None,
    ):
        video_content.seek(0, SEEK_END)
        video_sz = video_content.tell()
        video_content.seek(0, SEEK_SET)

        res = await self.generate_upload_shortcode(video_sz)

        if res.ok:
            res_json = await res.json()
            shortcode = res_json["shortcode"]
            access_key_id = res_json["credentials"]["accessKeyId"]
            secret_access_key = res_json["credentials"]["secretAccessKey"]
            session_token = res_json["credentials"]["sessionToken"]
            transcoder_token = res_json["transcoder_options"]["token"]

            res = await self.update_video_metadata(
                shortcode,
                video_filename,
                video_sz,
                video_title=video_title,
            )

            if res.ok:
                client(
                    "s3",
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    aws_session_token=session_token,
                ).upload_fileobj(
                    video_content,
                    "streamables-upload",
                    f"upload/{shortcode}",
                    ExtraArgs={"ACL": "public-read"},
                )

                res = await self.start_transcode_upload(
                    shortcode,
                    video_sz,
                    transcoder_token,
                )

        return res

    async def clip_video(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        res = await self.__session.get(
            f"{Streamable.api_url}/extract",
            params={"url": f"{Streamable.base_url}/{video_id}"},
        )

        if res.ok and (
            "error" not in (respJsonData := await res.json())
            or respJsonData["error"] is None
        ):
            shortcode_vid_url = respJsonData["url"]
            shortcode_vid_headers = respJsonData["headers"]

            res = await self.generate_streamable_clip_shortcode(
                video_id,
                mirror_title=mirror_title,
            )

            if res.ok or (
                "error" not in (respJsonData := await res.json())
                or respJsonData["error"] is None
            ):
                new_mirror_shortcode = respJsonData["shortcode"]

                res = await self.__session.post(
                    f"{Streamable.api_url}/transcode/{new_mirror_shortcode}",
                    json={
                        "extractor": "streamable",
                        "headers": shortcode_vid_headers,
                        "mute": False,
                        "shortcode": new_mirror_shortcode,
                        "thumb_offset": None,
                        "title": (
                            ""
                            if mirror_title is None
                            else mirror_title
                        ),
                        "upload_source": "clip",
                        "url": shortcode_vid_url,
                    },
                )

        return res

    async def clip_streamja_video(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        res = await self.__session.get(
            f"{Streamable.api_url}/extract",
            params={"url": f"{Streamja.base_url}/{video_id}"},
        )

        if res.ok and (
            "error" not in (respJsonData := await res.json())
            or respJsonData["error"] is None
        ):
            shortcode_vid_url = respJsonData["url"]
            shortcode_vid_headers = respJsonData["headers"]

            res = await self.generate_streamja_clip_shortcode(
                video_id,
                mirror_title=mirror_title,
            )

            if res.ok or (
                "error" not in (respJsonData := await res.json())
                or respJsonData["error"] is None
            ):
                new_mirror_shortcode = res.json()["shortcode"]

                res = await self.__session.post(
                    f"{Streamable.api_url}/transcode/{new_mirror_shortcode}",
                    json={
                        "extractor": "generic",
                        "headers": shortcode_vid_headers,
                        "mute": False,
                        "shortcode": new_mirror_shortcode,
                        "thumb_offset": None,
                        "title": (
                            ""
                            if mirror_title is None
                            else mirror_title
                        ),
                        "upload_source": "clip",
                        "url": shortcode_vid_url,
                    },
                )

        return res

    async def clip_streamwo_video(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        res = await self.__session.get(
            f"{Streamable.api_url}/extract",
            params={"url": f"{Streamwo.base_url}/{video_id}"},
        )

        if res.ok and (
            "error" not in (respJsonData := await res.json())
            or respJsonData["error"] is None
        ):
            shortcode_vid_url = respJsonData["url"]
            shortcode_vid_headers = respJsonData["headers"]

            res = await self.generate_streamwo_clip_shortcode(
                video_id,
                mirror_title=mirror_title,
            )

            if res.ok or (
                "error" not in (respJsonData := await res.json())
                or respJsonData["error"] is None
            ):
                new_mirror_shortcode = respJsonData["shortcode"]

                res = await self.__session.post(
                    f"{Streamable.api_url}/transcode/{new_mirror_shortcode}",
                    json={
                        "extractor": "generic",
                        "headers": shortcode_vid_headers,
                        "mute": False,
                        "shortcode": new_mirror_shortcode,
                        "thumb_offset": None,
                        "title": (
                            ""
                            if mirror_title is None
                            else mirror_title
                        ),
                        "upload_source": "clip",
                        "url": shortcode_vid_url,
                    },
                )

        return res

    async def clip_streamff_video(
        self,
        video_id: str,
        mirror_title: str = "",
    ):
        res = await self.__session.get(
            f"{Streamff.base_url}/api/videos/{video_id}",
        )

        if not res.ok:
            return res

        res = await self.__session.get(
            f"{Streamable.api_url}/extract",
            params={"url": res.json()["videoLink"]},
        )

        if res.ok and (
            "error" not in (respJsonData := await res.json())
            or respJsonData["error"] is None
        ):
            shortcode_vid_url = respJsonData["url"]
            shortcode_vid_headers = respJsonData["headers"]

            res = await self.generate_streamff_clip_shortcode(
                video_id,
                mirror_title=mirror_title,
            )

            if res.ok or (
                "error" not in (respJsonData := await res.json())
                or respJsonData["error"] is None
            ):
                new_mirror_shortcode = respJsonData["shortcode"]

                res = await self.__session.post(
                    f"{Streamable.api_url}/transcode/{new_mirror_shortcode}",
                    json={
                        "extractor": "generic",
                        "headers": shortcode_vid_headers,
                        "mute": False,
                        "shortcode": new_mirror_shortcode,
                        "thumb_offset": None,
                        "title": (
                            ""
                            if mirror_title is None
                            else mirror_title
                        ),
                        "upload_source": "clip",
                        "url": shortcode_vid_url,
                    },
                )

        return res

    async def poll_video_status(self, video_id: str):
        return await self.__session.get(
            f"{Streamable.api_url}/poll2",
            json=[
                {
                    "shortcode": video_id,
                    "version": 0,
                },
            ],
        )

    async def purge_complete(self, video_id: str):
        return await self.__session.put(
            f"{Streamable.api_url}/videos/{video_id}",
            params={"purge": ""},
            json={"upload_percent": 100},
        )

    async def get_video(self, video_id: str):
        res = await self.__session.get(f"{Streamable.base_url}/{video_id}")

        if not res.ok:
            return res

        return await self.__session.get(
            BeautifulSoup(
                await res.text(),
                features="html.parser",
            ).find_all(
                "meta",
                attrs={"property": "og:video:secure_url"},
            )[0]["content"]
        )


class Streamja:
    base_url = "https://streamja.com"

    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ):
        self.__session = _client_session_setup(
            session=session,
            user_agent=user_agent,
        )

    async def generate_upload_shortcode(self):
        return await self.__session.post(
            f"{Streamja.base_url}/shortId.php",
            data={"new": 1},
        )

    async def upload_from_file(self, video_path: Path):
        return await self.upload_video(
            video_path.open(mode="rb"), video_path.name,
        )

    async def upload_video(
        self,
        video_content: BytesIO | BufferedReader | StreamReader,
        video_filename: str,
    ):
        res = await self.generate_upload_shortcode()

        if res.ok and "error" not in (res_json := await res.json()):
            form_data = FormData()
            form_data.add_field(
                "file",
                video_content,
                content_type=guess_type(video_filename)[0],
                filename=video_filename,
            )

            res = await self.__session.post(
                f"{Streamja.base_url}/upload.php",
                params={"shortId": res_json["shortId"]},
                data=form_data,
            )

        return res

    async def get_video(self, video_id: str):
        res = await self.__session.get(f"{Streamja.base_url}/{video_id}")

        if not res.ok:
            return res

        return await self.__session.get(
            BeautifulSoup(
                await res.text(),
                features="html.parser",
            ).find_all("source")[0]["src"]
        )


class Streamwo:
    base_url = "https://streamwo.com"

    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ):
        self.__session = _client_session_setup(
            session=session,
            user_agent=user_agent,
        )

    @staticmethod
    def generate_upload_id():
        return "".join([choice(ascii_letters + digits) for _ in range(7)])

    async def upload_from_file(self, video_path: Path):
        return await self.upload_video(
            video_path.open(mode="rb"),
            video_path.name,
        )

    async def upload_video(
        self,
        video_content: BytesIO | BufferedReader | StreamReader,
        video_filename: str,
    ):
        form_data = FormData()
        form_data.add_field(
            "file",
            video_content,
            content_type=guess_type(video_filename)[0],
            filename=video_filename,
        )

        return await self.__session.post(
            f"{Streamwo.base_url}/index.php",
            params={
                "action": "upload",
                "id": Streamwo.generate_upload_id(),
            },
            data=form_data,
        )

    async def get_video(self, video_id: str):
        res = await self.__session.get(f"{Streamwo.base_url}/{video_id}")

        if not res.ok:
            return res

        return await self.__session.get(
            BeautifulSoup(
                await res.text(),
                features="html.parser",
            ).find_all("source")[0]["src"]
        )


class Streamff:
    base_url = "https://streamff.com"

    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ):
        self.__session = _client_session_setup(
            session,
            user_agent=user_agent,
        )

    async def generate_link(self):
        return await self.__session.post(
            f"{Streamff.base_url}/api/videos/generate-link"
        )

    async def upload_from_file(self, video_path: Path):
        return await self.upload_video(
            video_path.open(mode="rb"), video_path.name,
        )

    async def upload_video(
        self,
        video_content: BytesIO | BufferedReader | StreamReader,
        video_filename: str,
    ):
        res = await self.generate_link()

        if not res.ok:
            raise ValueError("Unexpected response!")

        form_data = FormData()
        form_data.add_field(
            "file",
            video_content,
            content_type=guess_type(video_filename)[0],
            filename=video_filename,
        )

        return await self.__session.post(
            f"{Streamff.base_url}/api/videos/upload/{await res.text()}",
            data=form_data,
        )

    async def get_video(self, video_id: str):
        res = await self.__session.get(
            f"{Streamff.base_url}/api/videos/{video_id}",
        )

        if not res.ok:
            return res

        return await self.__session.get(
            f'{Streamff.base_url}{(await res.json())["videoLink"]}'
        )
