import sys
import traceback

try:
    sys.path.insert(0, r"C:\Users\86187\Desktop\yuyi_pro_v2")
    from webapp.main import app
    print("IMPORT OK")
    # Check routes
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', set())
            print(f"  {methods} {route.path}")
except Exception as e:
    print(f"IMPORT FAILED: {e}")
    traceback.print_exc()
