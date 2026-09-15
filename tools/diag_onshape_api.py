"""Diagnostic: call Onshape get_assembly directly and print raw HTTP status/body preview.

Does NOT print API keys. Run from onshape_export/ directory (or anywhere; .env is
searched upward via find_dotenv like onshape-to-robot itself does).
"""
import sys
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

from onshape_to_robot.onshape_api.onshape import Onshape  # noqa: E402

DID = "d103e836077cf07efd7a6f0f"
WID = "5f12ac3c351e45b12f00dce2"
EID = "8f867c9398c906dbec790638"

stack = os.getenv("ONSHAPE_API")
print(f"ONSHAPE_API = {stack}")
print(f"ONSHAPE_ACCESS_KEY set = {bool(os.getenv('ONSHAPE_ACCESS_KEY'))}")
print(f"ONSHAPE_SECRET_KEY set = {bool(os.getenv('ONSHAPE_SECRET_KEY'))}")

api = Onshape(stack=stack, creds="./myrobot_dummy/config.json", logging=False)

path = f"/api/assemblies/d/{DID}/w/{WID}/e/{EID}"
query = {
    "includeMateFeatures": "true",
    "includeMateConnectors": "true",
    "includeNonSolids": "true",
    "configuration": "default",
}

req_headers = api._make_headers("get", path, query)
url = stack + path + "?" + "&".join(f"{k}={v}" for k, v in query.items())

import requests  # noqa: E402

res = requests.request("get", url, headers=req_headers, allow_redirects=False, stream=True)
print(f"status_code = {res.status_code}")
print(f"headers = {dict(res.headers)}")
print(f"content-length header = {res.headers.get('Content-Length')}")
text = res.text
print(f"body length = {len(text)}")
print(f"body preview (first 300 chars) = {text[:300]!r}")
