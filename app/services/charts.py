import mplfinance as mpf
import pandas as pd

def draw_chart(df, df_macd, path_png):
    apds = [
        mpf.make_addplot(df_macd['macd'], panel=1, color='b'),
        mpf.make_addplot(df_macd['signal'], panel=1, color='r'),
        mpf.make_addplot(df_macd['hist'], panel=1, type='bar', color='g'),
    ]
    mpf.plot(df, type='candle', addplot=apds, volume=True, style='yahoo',
             savefig=dict(fname=path_png, dpi=120, bbox_inches='tight'))
