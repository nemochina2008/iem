"""COOP period stats"""
import datetime
from collections import OrderedDict

import numpy as np
from pandas.io.sql import read_sql
from pyiem import network
from pyiem.util import get_autoplot_context, get_dbconn

PDICT = OrderedDict([
        ('avg_high_temp', 'Average High Temperature'),
        ('avg_low_temp', 'Average Low Temperature'),
        ('avg_temp', 'Average Temperature'),
        ('max_low', 'Maximum High Temperature'),
        ('min_low', 'Minimum Low Temperature'),
        ('days-high-above',
         'Days with High Temp Greater Than or Equal To (threshold)'),
        ('days-high-below', 'Days with High Temp Below (threshold)'),
        ('days-lows-above',
         'Days with Low Temp Greater Than or Equal To (threshold)'),
        ('days-lows-below', 'Days with Low Temp Below (threshold)'),
        ('precip', 'Total Precipitation')])


def get_description():
    """ Return a dict describing how to call this plotter """
    desc = dict()
    desc['data'] = True
    desc['description'] = """This plot presents statistics for a period of
    days each year provided your start date and number of days after that
    date. If your period crosses a year bounds, the plotted year represents
    the year of the start date of the period."""
    today = datetime.datetime.today() - datetime.timedelta(days=1)
    desc['arguments'] = [
        dict(type='station', name='station', default='IA2203',
             label='Select Station', network='IACLIMATE'),
        dict(type='month', name='month',
             default=(today - datetime.timedelta(days=14)).month,
             label='Start Month:'),
        dict(type='day', name='day',
             default=(today - datetime.timedelta(days=14)).day,
             label='Start Day:'),
        dict(type="int", name="days", default="14",
             label="Number of Days"),
        dict(type='select', name='varname', default='avg_temp',
             label='Variable to Compute:', options=PDICT),
        dict(type='float', name='thres', default=-99,
             label='Threshold (when appropriate):'),
        dict(type='year', name='year', default=today.year,
             label="Year to Highlight in Chart:"),
    ]
    return desc


def nice(val):
    """nice printer"""
    if val == 'M':
        return 'M'
    if val < 0.01 and val > 0:
        return 'Trace'
    return '%.2f' % (val, )


def plotter(fdict):
    """ Go """
    import matplotlib
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
    pgconn = get_dbconn('coop')
    ctx = get_autoplot_context(fdict, get_description())
    station = ctx['station']
    days = ctx['days']
    sts = datetime.date(2012, ctx['month'],
                        ctx['day'])
    ets = sts + datetime.timedelta(days=(days - 1))
    varname = ctx['varname']
    year = ctx['year']
    threshold = ctx['thres']
    table = "alldata_%s" % (station[:2],)
    nt = network.Table("%sCLIMATE" % (station[:2],))
    sdays = []
    for i in range(days):
        ts = sts + datetime.timedelta(days=i)
        sdays.append(ts.strftime("%m%d"))

    doff = (days + 1) if ets.year != sts.year else 0
    df = read_sql("""
    SELECT extract(year from day - '"""+str(doff)+""" days'::interval) as yr,
    avg((high+low)/2.) as avg_temp, avg(high) as avg_high_temp,
    avg(low) as avg_low_temp,
    sum(precip) as precip,
    min(low) as min_low,
    max(high) as max_high,
    sum(case when high >= %s then 1 else 0 end) as "days-high-above",
    sum(case when high < %s then 1 else 0 end) as "days-high-below",
    sum(case when low >= %s then 1 else 0 end) as "days-lows-above",
    sum(case when low < %s then 1 else 0 end) as "days-lows-below"
    from """ + table + """
    WHERE station = %s and sday in %s
    GROUP by yr ORDER by yr ASC
    """, pgconn, params=(threshold, threshold, threshold, threshold,
                         station, tuple(sdays)))

    (fig, ax) = plt.subplots(2, 1, figsize=(8, 6))

    bars = ax[0].bar(df['yr'], df[varname], facecolor='r', edgecolor='r')
    thisvalue = "M"
    for bar, x, y in zip(bars, df['yr'], df[varname]):
        if x == year:
            bar.set_facecolor('g')
            bar.set_edgecolor('g')
            thisvalue = y
    ax[0].set_xlabel("Year, %s = %s" % (year, nice(thisvalue)))
    ax[0].axhline(df[varname].mean(), lw=2,
                  label='Avg: %.2f' % (df[varname].mean(), ))
    ylabel = r"Temperature $^\circ$F"
    if varname in ['precip', ]:
        ylabel = "Precipitation [inch]"
    elif varname.find('days') > -1:
        ylabel = "Days"
    ax[0].set_ylabel(ylabel)
    title = PDICT.get(varname).replace("(threshold)", str(threshold))
    ax[0].set_title(("[%s] %s\n%s from %s through %s"
                     ) % (station, nt.sts[station]['name'], title,
                          sts.strftime("%d %b"), ets.strftime("%d %b")),
                    fontsize=12)
    ax[0].grid(True)
    ax[0].legend(ncol=2, fontsize=10)
    ax[0].set_xlim(df['yr'].min()-1, df['yr'].max()+1)
    rng = df[varname].max() - df[varname].min()
    ax[0].set_ylim(df[varname].min() - rng * .3,
                   df[varname].max() + rng * .3)
    box = ax[0].get_position()
    ax[0].set_position([box.x0, box.y0 + 0.02,
                        box.width, box.height * 0.98])

    # Plot 2: CDF
    X2 = np.sort(df[varname])
    ptile = np.percentile(df[varname], [0, 5, 50, 95, 100])
    N = len(df[varname])
    F2 = np.array(range(N))/float(N) * 100.
    ax[1].plot(X2, 100. - F2)
    ax[1].set_xlabel(ylabel)
    ax[1].set_ylabel("Observed Frequency [%]")
    ax[1].grid(True)
    ax[1].set_yticks([0, 5, 10, 25, 50, 75, 90, 95, 100])
    mysort = df.sort_values(by=varname, ascending=True)
    info = ("Min: %.2f %.0f\n95th: %.2f\nMean: %.2f\nSTD: %.2f\n5th: %.2f\n"
            "Max: %.2f %.0f"
            ) % (df[varname].min(), df['yr'][mysort.index[0]], ptile[1],
                 np.average(df[varname]), np.std(df[varname]),
                 ptile[3], df[varname].max(),
                 df['yr'][mysort.index[-1]])
    ax[1].text(0.8, 0.95, info, transform=ax[1].transAxes, va='top',
               bbox=dict(facecolor='white', edgecolor='k'))
    return fig, df


if __name__ == '__main__':
    plotter(dict())
