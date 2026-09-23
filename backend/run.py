import os

from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Do not expose the interactive debugger on a network.
    app.run(debug=(os.environ.get("APP_DEBUG") == "1" and os.environ.get("APP_HOST", "127.0.0.1") in ("127.0.0.1", "localhost", "::1")),
            host=os.environ.get("APP_HOST", "127.0.0.1"),
            port=int(os.environ.get("APP_PORT", "5666")))
