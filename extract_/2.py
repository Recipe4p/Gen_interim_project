from datetime import datetime, timedelta
import requests
import pandas as pd
import time

# 1. CONFIGURATION CLASS (centralize constants)
class RainfallConfig:
    API_URL = 'https://api-open.data.gov.sg/v2/real-time/api/rainfall'
    TIMEOUT = 10
    RATE_LIMIT_DELAY = 3
    RETRY_DELAY = 4

# 2. API HANDLER CLASS (single responsibility: API calls)
class RainfallAPIClient:
    def __init__(self, config=RainfallConfig):
        self.config = config
    
    def _make_request(self, params):
        """Centralized request logic - DRY principle"""
        try:
            response = requests.get(
                self.config.API_URL, 
                params=params, 
                timeout=self.config.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout for params: {params}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request failed: {e}")
    
    def get_stations(self, timestamp):
        """Get station data"""
        data = self._make_request({'date': timestamp})
        
        if data.get('code') != 0:
            raise ValueError(f"API error code: {data.get('code')}")
        
        stations_df = pd.json_normalize(
            data["data"], 
            record_path="stations", 
            sep="."
        )
        stations_df.rename(
            columns={
                'location.latitude': 'latitude',
                'location.longitude': 'longitude'
            },
            inplace=True
        )
        return stations_df
    
    def get_readings(self, timestamp):
        """Get reading data"""
        data = self._make_request({'date': timestamp})
        
        if data.get('code') != 0:
            raise ValueError(f"API error code: {data.get('code')}")
        
        readings = pd.json_normalize(
            data["data"]["readings"],
            record_path="data",
            meta="timestamp",
            sep=".",
            errors="ignore"
        )
        readings['query_timestamp'] = timestamp
        return readings

# 3. DATA PROCESSOR CLASS (single responsibility: transformations)
class DateProcessor:
    @staticmethod
    def create_dates(start_date, end_date):
        dates = pd.date_range(start=start_date, end=end_date)
        return dates.strftime("%Y-%m-%d").tolist()
    
    @staticmethod
    def create_timestamps(dates):
        timestamps = []
        for d in dates:
            dt = datetime.strptime(d, "%Y-%m-%d")
            for h in range(24):
                ts = dt + timedelta(hours=h)
                timestamps.append(ts.isoformat())
        return timestamps

# 4. ORCHESTRATOR CLASS (coordinates components)
class RainfallDataExtractor:
    def __init__(self, api_client=None, date_processor=None):
        self.api_client = api_client or RainfallAPIClient()
        self.date_processor = date_processor or DateProcessor()
    
    def extract(self, start_date, end_date):
        """Main orchestration method"""
        dates = self.date_processor.create_dates(start_date, end_date)
        timestamps = self.date_processor.create_timestamps(dates)
        
        # Get stations once
        stations_df = self.api_client.get_stations(timestamps[0])
        time.sleep(RainfallConfig.RATE_LIMIT_DELAY)
        
        # Get all readings
        readings_list = []
        for i, timestamp in enumerate(timestamps, 1):
            print(f"Pulling {i}/{len(timestamps)} — {timestamp}")
            try:
                readings = self.api_client.get_readings(timestamp)
                readings_list.append(readings)
            except (ValueError, ConnectionError, TimeoutError) as e:
                print(f"Error at {timestamp}: {e}")
                time.sleep(RainfallConfig.RETRY_DELAY)
                continue
            
            time.sleep(RainfallConfig.RATE_LIMIT_DELAY)
        
        readings_df = pd.concat(readings_list)
        return stations_df, readings_df

# USAGE:
if __name__ == "__main__":
    extractor = RainfallDataExtractor()
    stations_df, readings_df = extractor.extract('2025-01-01', '2025-01-02')
    
    stations_df.to_csv('rainfall/rain_stations.csv', index=False)
    print("Saved stations data")
    readings_df.to_csv('rainfall/rain_readings.csv', index=False)
    print("Saved readings data")