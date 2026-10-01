from Extract import RainfallDataExtractor

extractor = RainfallDataExtractor()

stations_df, readings_df = extractor.extract(
    start_date="2025-01-01",
    end_date="2025-01-02",
)

print(stations_df.to_string())
print(readings_df.to_string())