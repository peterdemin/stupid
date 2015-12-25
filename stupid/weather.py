import logging
import requests


logger = logging.getLogger(__name__)


class WeatherForecast(object):
    def __init__(self, token=None):
        self.token = token

    def report(self, latitude=38.9977, longitude=-77.0988):
        data = self.currently(latitude, longitude)
        return "{0:.0f} \u00B0F at {1:.1f} mph wind".format(
            data['apparentTemperature'],
            data['windSpeed'],
        )

    def currently(self, latitude, longitude):
        return self.forecast(latitude, longitude).json()['currently']

    def forecast(self, latitude, longitude):
        url = 'https://{url}/{token}/{latitude:.4f},{longitude:.4f}'.format(
            url='api.forecast.io/forecast',
            token=self.token,
            latitude=latitude,
            longitude=longitude,
        )
        logger.debug("Fetching %r", url)
        response = requests.get(url)
        logger.debug("Result %r", response.status_code)
        return response
