import sys
sys.path.insert(0, '/home/jes/control-plane')
from mcp_server import mcp
mcp.run(transport='stdio')
