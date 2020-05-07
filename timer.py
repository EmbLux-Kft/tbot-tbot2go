from datetime import datetime
import argparse
import sys
import time


def main() -> None:  # noqa: C901

    parser = argparse.ArgumentParser(description='return true if hour = hour')

    parser.add_argument(
        "-s",
        dest="stunde",
        type=str,
        help="stunde, when triggering",
    )

    parser.add_argument(
        "-m",
        dest="minute",
        type=str,
        help="minute, when triggering",
    )

    args = parser.parse_args()

    today = datetime.now()
    h = today.strftime("%H")
    m = today.strftime("%M")

    if h == args.stunde and m == args.minute:
        sys.exit(0)

    time.sleep(50)
    sys.exit(1)

if __name__ == "__main__":
    main()
