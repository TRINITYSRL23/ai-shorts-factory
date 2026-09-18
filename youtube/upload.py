#!/usr/bin/env python3
"""Upload (and optionally schedule) a finished video to YouTube.

Meant to be called by the automation agent after the faceless-video pipeline
has produced final.mp4 (+ optional thumbnail). Uses a pre-minted token.json
(see oauth_get_token.py / docs/OAUTH_SETUP.md) — never runs an interactive
OAuth flow itself, so it's safe to call from an unattended session.

Usage:
    python upload.py \
        --video work/output/final.mp4 \
        --title "1901년, 바다에서 건진 2천 년 전 아날로그 컴퓨터" \
        --description "..." \
        --tags "역사,과학,안티키테라" \
        --category-id 27 \
        --privacy private \
        --publish-at 2026-09-19T00:00:00Z \
        --thumbnail work/output/thumb.jpg
"""
import argparse
import http.client
import os
import random
import sys
import time

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)
RETRIABLE_STATUS_CODES = (500, 502, 503, 504, 403, 429)
MAX_RETRIES = 8


def load_credentials(token_path: str) -> Credentials:
    if not os.path.exists(token_path):
        print(
            f"error: {token_path} not found. Run oauth_get_token.py once first "
            "(see docs/OAUTH_SETUP.md) — this script never opens a browser.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def build_body(args: argparse.Namespace) -> dict:
    status = {
        "privacyStatus": "private" if args.publish_at else args.privacy,
        "selfDeclaredMadeForKids": args.made_for_kids,
    }
    if args.publish_at:
        status["publishAt"] = args.publish_at

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None

    return {
        "snippet": {
            "title": args.title,
            "description": args.description or "",
            "tags": tags,
            "categoryId": str(args.category_id),
        },
        "status": status,
    }


def upload_video(youtube, args: argparse.Namespace) -> str:
    body = build_body(args)
    media = MediaFileUpload(args.video, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    error = None
    retry = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  uploaded {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = str(e)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                print("error: too many retries, giving up.", file=sys.stderr)
                raise SystemExit(1)
            sleep_seconds = min(2**retry, 60) + random.random()
            print(f"  retriable error ({error}); retrying in {sleep_seconds:.1f}s", file=sys.stderr)
            time.sleep(sleep_seconds)
            error = None

    video_id = response["id"]
    print(f"Uploaded: https://youtu.be/{video_id} (id={video_id})")
    return video_id


def set_thumbnail(youtube, video_id: str, thumbnail_path: str) -> None:
    youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
    print(f"Thumbnail set from {thumbnail_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", required=True, help="Path to the finished mp4")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--category-id", type=int, default=27, help="YouTube category id (27=Education, 24=Entertainment, 22=People & Blogs)")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    parser.add_argument("--publish-at", default=None, help="RFC3339 timestamp (e.g. 2026-09-19T00:00:00Z) to schedule release; forces privacy=private until then")
    parser.add_argument("--made-for-kids", action="store_true")
    parser.add_argument("--thumbnail", default=None, help="Optional path to a thumbnail image")
    parser.add_argument("--token", default=os.environ.get("YT_TOKEN_PATH", "token.json"))
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"error: video file not found: {args.video}", file=sys.stderr)
        return 2

    creds = load_credentials(args.token)
    youtube = build("youtube", "v3", credentials=creds)

    video_id = upload_video(youtube, args)

    if args.thumbnail:
        if os.path.exists(args.thumbnail):
            set_thumbnail(youtube, video_id, args.thumbnail)
        else:
            print(f"warning: thumbnail not found, skipping: {args.thumbnail}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
