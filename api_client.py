import json
import gzip
import re
import urllib.request
import urllib.error
from .constants import ASSETS_API_URL, MULTIPART_BOUNDARY

def upload_model(api_key, file_data, name, creator_id, creator_type, model_id=None):
    """Uploads or Updates an FBX model via the Assets API."""
    
    if model_id:
        api_url = f"{ASSETS_API_URL}/{model_id}"
        method = 'PATCH'
        request_data = { "assetId": int(model_id) }
    else:
        api_url = ASSETS_API_URL
        method = 'POST'
        request_data = {
            "assetType": "Model",
            "displayName": name[:50],
            "description": "Blender Map Builder Asset",
            "creationContext": {
                "creator": { "userId" if creator_type == "USER" else "groupId": str(creator_id) }
            }
        }
    
    body = bytearray()
    body.extend(f"--{MULTIPART_BOUNDARY}\r\n".encode('utf-8'))
    body.extend(b"Content-Disposition: form-data; name=\"request\"\r\n")
    body.extend(b"Content-Type: application/json\r\n\r\n")
    body.extend(json.dumps(request_data).encode('utf-8'))
    body.extend(b"\r\n")
    
    body.extend(f"--{MULTIPART_BOUNDARY}\r\n".encode('utf-8'))
    body.extend(f"Content-Disposition: form-data; name=\"fileContent\"; filename=\"mesh.fbx\"\r\n".encode('utf-8'))
    body.extend(b"Content-Type: model/fbx\r\n\r\n")
    body.extend(file_data)
    body.extend(b"\r\n")
    body.extend(f"--{MULTIPART_BOUNDARY}--\r\n".encode('utf-8'))
    
    req = urllib.request.Request(api_url, data=body, method=method)
    req.add_header('x-api-key', api_key)
    req.add_header('Content-Type', f'multipart/form-data; boundary={MULTIPART_BOUNDARY}')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read())
            return f"https://apis.roblox.com/assets/v1/{res_data['path']}"
    except urllib.error.HTTPError as e:
        raise Exception(f"Upload Failed: {e.read().decode('utf-8')}")

def poll_operation(api_key, operation_url):
    """Checks the status of an ongoing upload operation."""
    req = urllib.request.Request(operation_url, method='GET')
    req.add_header('x-api-key', api_key)
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def download_and_extract_mesh_id(api_key, asset_id):
    """Hits the Asset Delivery API, downloads the model, and regexes the MeshId."""
    url = f"https://apis.roblox.com/asset-delivery-api/v1/assetId/{asset_id}"
    req = urllib.request.Request(url, method='GET')
    req.add_header('x-api-key', api_key)
    req.add_header('Accept', 'application/xml')
    
    with urllib.request.urlopen(req) as response:
        delivery_data = json.loads(response.read())
        location = delivery_data.get("location")
        
    if not location:
        raise Exception("No location returned from Asset Delivery API")
        
    cdn_req = urllib.request.Request(location, method='GET')
    cdn_req.add_header('Accept-Encoding', 'gzip')
    
    with urllib.request.urlopen(cdn_req) as cdn_response:
        raw_bytes = cdn_response.read()
        if cdn_response.info().get('Content-Encoding') == 'gzip':
            raw_bytes = gzip.decompress(raw_bytes)
            
    content_str = raw_bytes.decode('utf-8', errors='ignore')
    
    xml_pattern = r'name="MeshId"[^>]*>\s*<url>\s*(?:rbxassetid://|http://www\.roblox\.com/asset/\?id=)(\d+)'
    match = re.search(xml_pattern, content_str, re.IGNORECASE)
    
    if not match:
        near_pattern = r'MeshId.{0,100}?(?:rbxassetid://|id=)(\d+)'
        match = re.search(near_pattern, content_str, re.IGNORECASE | re.DOTALL)
        
    if not match:
        any_pattern = r'(?:rbxassetid://|id=)(\d+)'
        match = re.search(any_pattern, content_str, re.IGNORECASE)
        
    if match:
        return match.group(1)
    return None