import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import get_logger, log


def main():
    # Initialize logger (creates log file in logs/ directory)
    logger = get_logger()

    # Print startup message in terminal window
    log("==================================================")
    log("OpenROM v2.0 - Starting...")
    log("Universal ROM Compression Suite by M5 Dev")
    log(f"Log File: {logger.log_filepath}")
    log("==================================================")

    from ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
