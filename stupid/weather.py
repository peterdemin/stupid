import logging
import requests
from stupid.settings import WEATHER_TOKEN


logger = logging.getLogger(__name__)


class WeatherForecast(object):
    def __init__(self, token=None):
        self.token = token or WEATHER_TOKEN

    def report(self, latitude=38.9977, longitude=-77.0988):
        """
        Example output:
        {
            "time": 1451923306,
            "summary": "Mostly Cloudy",
            "icon": "partly-cloudy-day",
            "nearestStormDistance": 12,
            "nearestStormBearing": 175,
            "precipIntensity": 0,
            "precipProbability": 0,
            "temperature": 32.54,
            "apparentTemperature": 25.88,
            "dewPoint": 15.6,
            "humidity": 0.49,
            "windSpeed": 7.4,
            "windBearing": 319,
            "visibility": 10,
            "cloudCover": 0.66,
            "pressure": 1019.91,
            "ozone": 337.97
        }
        """
        data = self.currently(latitude, longitude)
        result = "{0:.0f} \u00B0F".format(data['apparentTemperature'])
        if data['windSpeed'] >= 2.0:
            result += " at {0:.1f} mph wind".format(data['windSpeed'])
        if data['precipProbability'] > 0:
            result += " and I am {0:.0f}% sure it is {1}".format(
                data['precipProbability'] * 100,
                "raining" if data['temperature'] > 32.0 else "snowing")
        return result

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
