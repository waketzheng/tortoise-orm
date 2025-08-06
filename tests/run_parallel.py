#!/usr/bin/env python
"""
Use multiprocessing to run shell command parallel.

Usage::
    $ python <me>.py test_sqlite test_mysql
"""

import concurrent.futures
import subprocess
import sys
from pathlib import Path

WORK_DIR = Path(__file__).parent.parent


def main() -> int:
    if not sys.argv[1:]:
        print(__doc__.replace("<me>", Path(__file__).stem))
        return 1
    cmds = [["make", i] for i in sys.argv[1:]]
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(cmds)) as executor:
        future_to_target = {executor.submit(subprocess.call, cmd): cmd[1] for cmd in cmds}
        for future in concurrent.futures.as_completed(future_to_target):
            target = future_to_target[future]
            try:
                rc = future.result()
            except Exception as exc:
                print(f"Runing {target} generated an exception: {exc}")
                raise exc
            else:
                if rc != 0:
                    return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
