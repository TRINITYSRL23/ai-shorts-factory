#!/usr/bin/env python3
"""One-time interactive OAuth flow to mint token.json for YouTube uploads.

Run this once, locally, as the Google account that owns the target YouTube
channel. It is not meant to run inside an unattended/scheduled session.

Usage:
    python oauth_get_token.py --client-secret client_secret.json --out token.json
"""
import argparse
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-secret", required=True, help="Path to client_secret.json downloaded from Google Cloud Console")
    parser.add_argument("--out", default="token.json", help="Where to write the resulting token (default: token.json)")
    parser.add_argument("--no-browser", action="store_true", help="Print a URL instead of opening a local browser (for headless/remote environments)")
    args = parser.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, SCOPES)

    if args.no_browser:
        creds = flow.run_console()
    else:
        try:
            creds = flow.run_local_server(port=0)
        except Exception as exc:  # no display / port bind failure in a remote box
            print(f"Local server flow failed ({exc}); falling back to console flow.", file=sys.stderr)
            creds = flow.run_console()

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"Saved credentials to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
