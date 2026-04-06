#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jes/control-plane')
import uvicorn
from mcp_server import mcp
uvicorn.run(mcp.streamable_http_app(), host='0.0.0.0', port=8001)
