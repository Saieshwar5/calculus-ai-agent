import uvicorn
import os
from pathlib import Path


if __name__ == "__main__":
    
    base_dir = Path(__file__).parent
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() != "false"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(base_dir / "app")],  # Watch app directory for changes
        log_level="info"
    )