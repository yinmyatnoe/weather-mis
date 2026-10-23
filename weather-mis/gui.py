"""Event-driven graphical user interface built with tkinter."""

import tkinter as tk
from collections import Counter
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from analyzer import ClimateAnalyzer
from standards import DISPLAY_NAMES, POLLUTANTS, VARIABLES


class WeatherApp:
    """Main window of the HCMC Climate Data Monitoring System."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HCMC Climate Data Monitoring System")
        self.root.geometry("1100x760")
        self._analyzer = ClimateAnalyzer()
        self._is_analysed = False
        self._build_widgets()

    def _build_widgets(self):
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill="x")
        ttk.Button(controls, text="Load CSV",
                   command=self.on_load_click).pack(side="left", padx=4)
        ttk.Button(controls, text="Analyse",
                   command=self.on_analyse_click).pack(side="left", padx=4)
        ttk.Button(controls, text="Show chart",
                   command=self.on_chart_click).pack(side="left", padx=4)
        ttk.Label(controls, text="Pollutant:").pack(side="left", padx=(16, 4))
        self._pollutant_names = {DISPLAY_NAMES[p]: p for p in POLLUTANTS}
        self._pollutant_box = ttk.Combobox(
            controls, values=list(self._pollutant_names), state="readonly")
        self._pollutant_box.current(0)
        self._pollutant_box.pack(side="left")

        self._status_label = ttk.Label(self.root, text="Status: no file loaded",
                                       padding=(12, 0))
        self._status_label.pack(fill="x")

        middle = ttk.Frame(self.root, padding=8)
        middle.pack(fill="both", expand=True)
        summary_frame = ttk.LabelFrame(middle, text="Monthly summary")
        summary_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        columns = ("month", "variable", "min", "max", "average")
        self._summary_table = ttk.Treeview(summary_frame, columns=columns,
                                           show="headings", height=12)
        for column in columns:
            self._summary_table.heading(column, text=column.capitalize())
            self._summary_table.column(column, width=110, anchor="center")
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical",
                                       command=self._summary_table.yview)
        self._summary_table.configure(yscrollcommand=summary_scroll.set)
        self._summary_table.pack(side="left", fill="both", expand=True)
        summary_scroll.pack(side="right", fill="y")

        alert_frame = ttk.LabelFrame(middle, text="Alerts")
        alert_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self._alert_list = tk.Listbox(alert_frame, height=12)
        alert_scroll = ttk.Scrollbar(alert_frame, orient="vertical",
                                     command=self._alert_list.yview)
        self._alert_list.configure(yscrollcommand=alert_scroll.set)
        self._alert_list.pack(side="left", fill="both", expand=True)
        alert_scroll.pack(side="right", fill="y")

        chart_frame = ttk.LabelFrame(self.root, text="Chart", padding=4)
        chart_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._figure = Figure(figsize=(9, 3.2))
        self._canvas = FigureCanvasTkAgg(self._figure, master=chart_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    # ----- Event handlers -----
    def on_load_click(self):
        """Ask for a CSV file, then load and validate it."""
        file_path = filedialog.askopenfilename(
            title="Select hourly data file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not file_path:
            return
        try:
            count = self._analyzer.load(file_path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Load error", f"Could not load file:\n{error}")
            return
        self._is_analysed = False
        self._summary_table.delete(*self._summary_table.get_children())
        self._alert_list.delete(0, tk.END)
        errors = self._analyzer.error_log
        reasons = Counter(reason for *_, reason in errors)
        detail = ", ".join(f"{reason}: {n}" for reason, n in reasons.items())
        self._status_label.config(
            text=f"Status: {count:,} records loaded | {len(errors)} invalid "
                 f"values excluded ({detail or 'none'})")

    def on_analyse_click(self):
        """Aggregate the data, calculate statistics and detect alerts."""
        if self._analyzer.record_count == 0:
            messagebox.showwarning("No data", "Please load a CSV file first.")
            return
        self._analyzer.aggregate_daily()
        self._analyzer.detect_exceedances()
        self._is_analysed = True
        self._show_summary()
        self._show_alerts()

    def on_chart_click(self):
        """Draw the chart for the selected pollutant."""
        if not self._is_analysed:
            messagebox.showwarning("No results", "Please click Analyse first.")
            return
        pollutant = self._pollutant_names[self._pollutant_box.get()]
        self._analyzer.plot_pollutant(pollutant, self._figure)
        self._canvas.draw()

    # ----- Display helpers -----
    def _show_summary(self):
        self._summary_table.delete(*self._summary_table.get_children())
        for variable in VARIABLES:
            for month, stats in self._analyzer.monthly_statistics(
                    variable).items():
                if stats is None:
                    row = (month, DISPLAY_NAMES[variable], "-", "-", "-")
                else:
                    row = (month, DISPLAY_NAMES[variable],
                           f"{stats['min']:.1f}", f"{stats['max']:.1f}",
                           f"{stats['average']:.1f}")
                self._summary_table.insert("", tk.END, values=row)

    def _show_alerts(self):
        self._alert_list.delete(0, tk.END)
        alerts = self._analyzer.alerts
        self._alert_list.insert(tk.END, f"{len(alerts)} alerts in total")
        for alert in alerts:
            self._alert_list.insert(tk.END, str(alert))

    def run(self):
        """Start the tkinter event loop."""
        self.root.mainloop()
