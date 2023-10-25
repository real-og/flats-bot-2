import pandas as pd


csv_file = 'src/service/ads.csv'


def analyze_minsk_advertisements(csv_file):
    df = pd.read_csv(csv_file)

    df['date'] = pd.to_datetime(df['date'])

    ads_minsk_df = df[(df['town'] == 'Минск') &
                      (df['cost'] <= 2000) &
                      (df['rooms_amount'] == '1')]

    daily_statistics = ads_minsk_df.groupby(ads_minsk_df['date'].dt.date).agg(
        total_advertisements=pd.NamedAgg(column='date', aggfunc='count'),
        average_price=pd.NamedAgg(column='cost', aggfunc='median')
    )

    return daily_statistics
