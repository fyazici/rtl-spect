# rtl-spect
A simple RTL-SDR spectrum analyzer tool inspired from [QSpectrumAnalyzer](https://github.com/xmikos/qspectrumanalyzer).

This is not a fork, only the user interface is similar in design to xmikos's project. Backend is rtl_power_fftw (MinGW build with required DLLs is provided in the [bundle.zip](bundle.zip)).
I developed this tool to add the features I need and/or frequently use.

Such features include:
* Easily and quickly setting the baseline through the GUI. Baseline is subtracted directly in the GUI without interrupting the scan.
* A running cursor for indicating the current position of the scan frequency.
* No waterfall plot as I find it distracting while tuning filters and often disable it.

TODO:
* Multiple cursor support with delta information.
* Ability to save and load baseline from files
* More efficient way to store frequency data and possibility to interpolate/resample baseline
