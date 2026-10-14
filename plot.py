"""Age panels styled after the supplied Figure 3 slide.

Run get_data.py first. Requires pandas/matplotlib. Overall lines use published
age aggregates, never unweighted means of quintile indices. Nov 2022–Jun 2026.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
AGES = [('Early Career 1 (22-25)', 'Early Career 1 (22–25)'),
        ('Senior (50+)', 'Senior (50+)')]
COLORS = ['#cccccc', '#b0b0b0', '#939393', '#737373', '#4d4d4d']


def exposure_legend(ax):
    legend = ax.inset_axes([.03, .78, .48, .19], zorder=10)
    legend.set_facecolor('white')
    legend.set_xlim(0, 1)
    legend.set_ylim(0, 1)
    legend.set_xticks([])
    legend.set_yticks([])
    for spine in legend.spines.values():
        spine.set_color('#888888')
        spine.set_linewidth(.7)
        spine.set_linestyle(':')
    cmap = LinearSegmentedColormap.from_list('exposure', COLORS)
    legend.imshow(np.linspace(0, 1, 256).reshape(1, -1), cmap=cmap,
                  extent=(.32, .67, .57, .77), aspect='auto', origin='lower')
    legend.text(.025, .67, 'Less\nexposed', va='center', fontsize=9, linespacing=1)
    legend.text(.70, .67, 'More\nexposed', va='center', fontsize=9, linespacing=1)
    legend.text(.025, .22, 'Overall', va='center', fontsize=9)
    legend.plot([.32, .67], [.22, .22], color='#ff4c4c', linewidth=1.4)


def main():
    df = pd.read_csv(ROOT / 'data' / 'canaries.csv', parse_dates=['observation_date'])
    manifest = json.loads((ROOT / 'data' / 'canaries_manifest.json').read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.edgecolor': '#888888', 'axes.linewidth': .8})
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    fig.subplots_adjust(left=.08, right=.96, bottom=.29, top=.79, wspace=.20)
    endpoints = []
    for ax, (age, title) in zip(axes, AGES):
        lines = [('AI exposure', q, COLORS[q-1]) for q in range(1, 6)]
        lines.append(('Overall', 0, '#ff4c4c'))
        for measure, quintile, color in lines:
            s = df[(df.measure == measure) & (df.age_group == age)
                   & (df.quintile == quintile)].sort_values('observation_date')
            if len(s) != 44 or s.observation_date.duplicated().any():
                raise ValueError('Expected 44 unique months for each plotted series')
            ax.plot(s.observation_date, s.employment_index / 100, color=color,
                    linewidth=1.4 if measure == 'Overall' else 1.1,
                    zorder=4 if measure == 'Overall' else 3)
            last = s.iloc[-1]
            endpoints.append(dict(measure=measure, age_group=age, quintile=quintile,
                                  date=last.observation_date.strftime('%Y-%m-%d'),
                                  headcount_index=last.employment_index / 100,
                                  change_percent=last.change_percent))
        ax.set_title(title, fontsize=13, pad=4)
        ax.set_ylabel('Headcount')
        ax.set_xlabel('Date', labelpad=4)
        ax.set_ylim(.7, 1.25)
        ax.set_xlim(pd.Timestamp('2022-11-01'), pd.Timestamp('2026-09-01'))
        ax.yaxis.set_major_locator(MultipleLocator(.1))
        ax.yaxis.set_minor_locator(MultipleLocator(.05))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        ax.tick_params(axis='y', labelleft=True)
        ax.tick_params(axis='x', labelrotation=90, labelsize=9)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.grid(axis='y', which='major', color='#dddddd', linewidth=.7)
        ax.grid(axis='y', which='minor', color='#eeeeee', linewidth=.5)
        ax.axvline(pd.Timestamp('2022-11-01'), color='#777777', linewidth=1)
        exposure_legend(ax)
    fig.text(.04, .91, 'Fact 2: young workers in exposed jobs', color='#9c1919',
             fontsize=25, fontfamily='DejaVu Serif', fontweight='bold')
    vintage = ', '.join(sorted(df.vintage.unique()))
    fig.text(.04, .065,
             'Employment indexed to 1 in November 2022; five exposure quintiles (light = less, dark = more exposed).\n'
             f"Source: Stanford / ADP Canaries Dashboard, release {manifest['release']}, vintage {vintage}.\n"
             'November 2022–June 2026. Dashboard sample differs from Brynjolfsson, Chandar & Chen (Aug 2026); descriptive trends.',
             fontsize=9, color='#666666', linespacing=1.5)
    fig.savefig(ROOT / 'figure.png', dpi=180, facecolor='white')
    pd.DataFrame(endpoints).to_csv(ROOT / 'data' / 'canaries_endpoints.csv', index=False)
    print(pd.DataFrame(endpoints).to_string(index=False))
    plt.close(fig)


if __name__ == '__main__':
    main()
