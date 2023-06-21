from rtl_spect.RtlScanThread import RtlScanThread
from rtl_spect.SpectrumPlot import SpectrumPlot

from typing import Dict

from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QPushButton,
    QDoubleSpinBox,
    QWidget,
    QFormLayout,
    QHBoxLayout,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RTL-SDR Spectrum Analyzer")
        self.setGeometry(100, 100, 800, 480)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self._init_layout()

        self.last_freq = "-"
        self.cursor_freq_mhz = "-"
        self.cursor_gain = "-"
        self.scan_thread = None
        self.running = False

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()

    def _init_layout(self):
        self.spectrum = SpectrumPlot()
        self.spectrum.cursor_move.connect(self._cursor_move)

        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self._start_click)

        self.btn_single = QPushButton("Single")
        self.btn_single.clicked.connect(self._single_click)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self._stop_click)
        self.btn_stop.setEnabled(False)

        self.spin_start = QDoubleSpinBox()
        self.spin_start.setMinimumSize(75, 0)
        self.spin_start.setDecimals(3)
        self.spin_start.setMinimum(30)
        self.spin_start.setMaximum(1800)
        self.spin_start.setValue(88)
        self.spin_start.valueChanged.connect(self._change_plot_limits)

        self.spin_end = QDoubleSpinBox()
        self.spin_end.setMinimumSize(75, 0)
        self.spin_end.setDecimals(3)
        self.spin_end.setMinimum(30)
        self.spin_end.setMaximum(1800)
        self.spin_end.setValue(108)
        self.spin_end.valueChanged.connect(self._change_plot_limits)

        self.spin_rbw = QDoubleSpinBox()
        self.spin_rbw.setMinimumSize(75, 0)
        self.spin_rbw.setDecimals(3)
        self.spin_rbw.setMinimum(1)
        self.spin_rbw.setMaximum(3200)
        self.spin_rbw.setValue(10)

        self.spin_rate = QDoubleSpinBox()
        self.spin_rate.setMinimumSize(75, 0)
        self.spin_rate.setDecimals(3)
        self.spin_rate.setMinimum(0.25)
        self.spin_rate.setMaximum(3.2)
        self.spin_rate.setValue(2.4)

        self.spin_gain = QDoubleSpinBox()
        self.spin_gain.setMinimumSize(75, 0)
        self.spin_gain.setDecimals(1)
        self.spin_gain.setMinimum(0)
        self.spin_gain.setMaximum(50)
        self.spin_gain.setValue(0)

        self.spin_repeats = QDoubleSpinBox()
        self.spin_repeats.setMinimumSize(75, 0)
        self.spin_repeats.setDecimals(0)
        self.spin_repeats.setMinimum(1)
        self.spin_repeats.setMaximum(1000)
        self.spin_repeats.setValue(100)

        self.spin_ppm = QDoubleSpinBox()
        self.spin_ppm.setMinimumSize(75, 0)
        self.spin_ppm.setDecimals(0)
        self.spin_ppm.setMinimum(-100)
        self.spin_ppm.setMaximum(100)
        self.spin_ppm.setValue(37)

        self.spin_plot_min = QDoubleSpinBox()
        self.spin_plot_min.setMinimumSize(75, 0)
        self.spin_plot_min.setDecimals(1)
        self.spin_plot_min.setMinimum(-100)
        self.spin_plot_min.setMaximum(100)
        self.spin_plot_min.setValue(-80)
        self.spin_plot_min.valueChanged.connect(self._change_plot_limits)

        self.spin_plot_max = QDoubleSpinBox()
        self.spin_plot_max.setMinimumSize(75, 0)
        self.spin_plot_max.setDecimals(1)
        self.spin_plot_max.setMinimum(-100)
        self.spin_plot_max.setMaximum(100)
        self.spin_plot_max.setValue(0)
        self.spin_plot_max.valueChanged.connect(self._change_plot_limits)

        self.btn_baseline_save = QPushButton("Save Baseline")
        self.btn_baseline_save.clicked.connect(self._baseline_save)

        self.btn_baseline_reset = QPushButton("Reset Baseline")
        self.btn_baseline_reset.clicked.connect(self._baseline_reset)
        
        self.form = QFormLayout()
        self.form.addRow(self.btn_start)
        self.form.addRow(self.btn_single)
        self.form.addRow(self.btn_stop)
        self.form.addRow("start [MHz]", self.spin_start)
        self.form.addRow("end [MHz]", self.spin_end)
        self.form.addRow("rbw [kHz]", self.spin_rbw)
        self.form.addRow("rate [Msps]", self.spin_rate)
        self.form.addRow("gain [dB]", self.spin_gain)
        self.form.addRow("repeats", self.spin_repeats)
        self.form.addRow("ppm", self.spin_ppm)
        self.form.addRow(self.btn_baseline_save)
        self.form.addRow(self.btn_baseline_reset)
        self.form.addRow("plot max [dB]", self.spin_plot_max)
        self.form.addRow("plot min [dB]", self.spin_plot_min)

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.spectrum, 1)
        self.hbox.addLayout(self.form, 0)

        self.main_widget.setLayout(self.hbox)

    def _set_running(self, v: bool):
        self.btn_start.setEnabled(not v)
        self.btn_single.setEnabled(not v)
        self.btn_stop.setEnabled(v)
        self.running = v
        self._update_status()

    def _update_status(self):
        if self.running:
            s0 = "Status: running"
        else:
            s0 = "Status: ready"
        s1 = f"scan freq: {self.last_freq}"
        s2 = f"cursor: ({self.cursor_freq_mhz} MHz, {self.cursor_gain} dB)"
        s = " | ".join((s0, s1, s2))
        self.status.showMessage(s)

    def _start_click(self, state):
        self._set_running(True)
        self._start_scan(True)

    def _single_click(self, state):
        self._set_running(True)
        self._start_scan(False)

    def _stop_click(self, state):
        self._stop_scan()

    def _start_scan(self, cont: bool):
        start = self.spin_start.value() * 1e6
        end = self.spin_end.value() * 1e6
        rate = self.spin_rate.value() * 1e6
        rbw = self.spin_rbw.value() * 1e3
        bins = rate / rbw
        gain = self.spin_gain.value() * 10
        repeats = self.spin_repeats.value()
        ppm = self.spin_ppm.value()

        self.spectrum.clear_data()
        self._change_plot_limits()

        self.scan_thread = RtlScanThread(
            start_freq=int(start),
            end_freq=int(end),
            sample_rate=int(rate),
            bins=int(bins),
            gain=int(gain),
            continuous=int(cont),
            repeats=int(repeats),
            ppm=int(ppm),
        )
        self.scan_thread.update_data.connect(self._update_data)
        self.scan_thread.finished.connect(self._scan_finished)
        self.scan_thread.start()

    def _stop_scan(self):
        self.scan_thread.requestInterruption()

    def _update_data(self, data: Dict[float, float]):
        f = sorted(data)[-1]
        self.last_freq = round(f / 1e6, 3)
        self.spectrum.add_data(data)
        self.spectrum.set_vcursor(f)
        self._update_status()

    def _scan_finished(self):
        self.last_freq = "-"
        self.last_sweep_time = "-"
        self._set_running(False)
        self._update_status()

    def _cursor_move(self, pt):
        if pt is not None:
            freq, gain = pt
            self.cursor_freq_mhz = round(freq / 1e6, 3)
            self.cursor_gain = round(gain, 3)
            self._update_status()
    
    def _baseline_save(self):
        self.spectrum.save_baseline()

    def _baseline_reset(self):
        self.spectrum.reset_baseline()

    def _change_plot_limits(self):
        start = self.spin_start.value() * 1e6
        end = self.spin_end.value() * 1e6
        plot_max = self.spin_plot_max.value()
        plot_min = self.spin_plot_min.value()
        self.spectrum.set_x_lim(start, end)
        self.spectrum.set_y_lim(plot_min, plot_max)
