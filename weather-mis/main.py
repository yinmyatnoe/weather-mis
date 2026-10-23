"""Entry point of the HCMC Climate Data Monitoring System."""

from gui import WeatherApp


def main():
    """Create the application window and start the event loop."""
    app = WeatherApp()
    app.run()


if __name__ == "__main__":
    main()
