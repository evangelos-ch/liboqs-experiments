import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import oqs

CSVs_TO_OPEN = ["oqs_bench/testing/results/KEMDTLS results.csv"]
RESULTS_FOLDER = "visualizations/pi/"

# Load data to pandas
frames = []
for _file in CSVs_TO_OPEN:
    frames.append(pd.read_csv(_file, index_col=0))
data = pd.concat(frames).reset_index()

# Get Claimed NIST level
def get_nist_level(kem):
    with oqs.KeyEncapsulation(kem) as client:
        level = client.details["claimed_nist_level"]
    return level
data["Claimed NIST Level"] = data["index"].map(lambda i: str(get_nist_level(i)))

palette = sns.color_palette("mako", len(data["index"].unique()))
palette = {category: colour for colour, category in zip(palette, sorted(data["index"].unique()))}

def generate_barplot(df, metric, metric_std, title, ax1, group=None, legend_title=None):
    sns.set_style("whitegrid")
    if metric_std:
        metric_std = df[metric_std]
    _palette = palette if not group else "mako"
    ax = sns.barplot(y="index", x=metric, hue=group, xerr=metric_std, data=df, ci=None, ax=ax1, palette=_palette)
    ax.set(xlabel=title[0], ylabel=title[1])
    if legend_title is not None:
        ax.legend().set(title=legend_title)

# KEM Encryption
fig, ax = plt.subplots(len(data["Claimed NIST Level"].unique()), figsize=(20, 30))

encrypt_timing_data = data.sort_values(by="Time")
for i, level in enumerate(sorted(data["Claimed NIST Level"].unique())):
    encrypt_timing_data_sub = encrypt_timing_data[encrypt_timing_data["Claimed NIST Level"] == level]
    generate_barplot(encrypt_timing_data_sub, "Time", None, ('Handshake Time (ms)', 'KEM'), ax[i])
    ax[i].title.set_text(f"NIST Level {level}")

fig.savefig(RESULTS_FOLDER + "handshake time.png")

# KEM Decryption
fig, ax = plt.subplots(len(data["Claimed NIST Level"].unique()), figsize=(20, 30))

decrypt_timing_data = data.sort_values(by="Network Bandwidth")
for i, level in enumerate(sorted(data["Claimed NIST Level"].unique())):
    decrypt_timing_data_sub = decrypt_timing_data[decrypt_timing_data["Claimed NIST Level"] == level]
    generate_barplot(decrypt_timing_data_sub, "Network Bandwidth", None, ('Network Bandwidth (bytes)', 'KEM'), ax[i])
    ax[i].title.set_text(f"NIST Level {level}")

fig.savefig(RESULTS_FOLDER + "bandwidth.png")
