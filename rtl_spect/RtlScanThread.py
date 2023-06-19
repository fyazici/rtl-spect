import sys
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal


class RtlScanThread(QThread):
    RTL_POWER_FFTW_EXECUTABLE = "./bundle/rtl_power_fftw.exe"

    update_data = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(
        self,
        /,
        start_freq: int,
        end_freq: int,
        sample_rate: int,
        bins: int,
        gain: int,
        continuous: bool,
        repeats: int,
        ppm: int,
        line_buffer_len: int = 10,
        parent=None,
        **kwargs,
    ):
        super().__init__(parent)
        self.args = [
            self.RTL_POWER_FFTW_EXECUTABLE,
            f"-f {start_freq}:{end_freq}",
            f"-r {sample_rate}",
            f"-b {bins}",
            f"-g {gain}",
            f"-n {repeats}",
            f"-p {ppm}",
        ]
        if continuous:
            self.args.append("-c")
        for k, v in kwargs.items():
            self.args.append(f"--{k} {v}")
        self.line_buffer_len = line_buffer_len

    def run(self):
        proc = subprocess.Popen(
            self.args, stdout=subprocess.PIPE, stderr=None, text=True
        )
        self.running = True

        data = {}
        while proc.poll() is None:
            if self.isInterruptionRequested():
                proc.terminate()
                if len(data) > 0:
                    self.update_data.emit(data)
                break
            elif len(data) < self.line_buffer_len:
                line = proc.stdout.readline().strip()
                try:
                    if len(line) > 0 and line[0] != "#":
                        f, m = line.split()[:2]
                        data[float(f)] = float(m)
                except Exception as e:
                    print(f"warn: while parsing rtl_power output: {e}", file=sys.stderr)
            else:
                self.update_data.emit(data)
                data = {}
        self.finished.emit()
