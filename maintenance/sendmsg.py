#!/usr/bin/env python3
import sys
import requests
import plac


@plac.pos("url", "Target URL")
@plac.pos("content_type", "Content-Type")
@plac.pos("payload", "HTTP body")
def main(url: str, content_type: str, payload: str):
    resp = requests.post(url, data=payload, headers={"Content-Type": content_type})

    if resp.status_code > 299 or resp.status_code < 200:
        print("Webhook failed with error:", resp.status_code, file=sys.stderr)
        print(":", resp.content, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    plac.call(main)
