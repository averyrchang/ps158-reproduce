# ps158-reproduce

Recreates the layout of Figure 3's early-career (22–25) and senior (50+) panels in Brynjolfsson, Chandar & Chen, [*Canaries in the Coal Mine?* (August 2026)](https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf), for November 2022–June 2026.

Data: original public [Stanford Digital Economy Lab / ADP Canaries Dashboard](https://digitaleconomy.stanford.edu/project/indicators/canaries-dashboard/) downloads, archived July 2026 release (vintage July 16). These dashboard aggregates use a different sample from the paper, so this is a reproduction of the presentation, not its exact numerical results. Gray lines show five AI exposure quintiles; red shows overall employment; November 2022 = 1.

Run `python -m pip install pandas matplotlib`, then `python get_data.py` and `python plot.py` (requires `curl`). The downloader saves source archives and provenance in `data/`; the plotter writes `figure.png`.

