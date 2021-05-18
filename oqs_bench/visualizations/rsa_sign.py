import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import oqs

CSVs_TO_OPEN = ["oqs_bench/testing/results/pi/sign/RSA.csv"]
RESULTS_FOLDER = "visualizations/pi/sign/"

# Load data to pandas
frames = []
for _file in CSVs_TO_OPEN:
    frames.append(pd.read_csv(_file, index_col=0))
data = pd.concat(frames).reset_index()
data["index"] = data["index"].map(lambda i: str(i))
print(data.head())

palette = sns.color_palette("mako", len(data["index"].unique()))
# palette = {category: colour for colour, category in zip(palette, sorted(data["index"].unique()))}
# print(palette)

def generate_barplot(df, metric, metric_std, title, ax1, group=None, legend_title=None):
    sns.set_style("whitegrid")
    if metric_std:
        metric_std = df[metric_std]
    _palette = palette if not group else "mako"
    ax = sns.barplot(y="index", x=metric, hue=group, xerr=metric_std, data=df, ci=None, ax=ax1, palette=_palette)
    ax.set(xlabel=title[0], ylabel=title[1])
    if legend_title is not None:
        ax.legend().set(title=legend_title)

# DSS Encryption
fig, ax = plt.subplots(figsize=(20, 10))

encrypt_timing_data = data.sort_values(by="Mean Encapsulation Time")
encrypt_timing_data["Mean Encapsulation Time"] /= 1_000_000
encrypt_timing_data["Encapsulation Time Standard Deviation"] /= 1_000_000
generate_barplot(encrypt_timing_data, "Mean Encapsulation Time", "Encapsulation Time Standard Deviation", ('Mean Signing CPU Time (ms)', 'DSS'), ax)

fig.savefig(RESULTS_FOLDER + "RSA sign time.png")

# DSS Decryption
fig, ax = plt.subplots(figsize=(20, 10))

decrypt_timing_data = data.sort_values(by="Mean Verification Time")
decrypt_timing_data["Mean Verification Time"] /= 1_000_000
decrypt_timing_data["Verification Time Standard Deviation"] /= 1_000_000
generate_barplot(decrypt_timing_data, "Mean Verification Time", "Verification Time Standard Deviation", ('Mean Verification CPU Time (ms)', 'DSS'), ax)

fig.savefig(RESULTS_FOLDER + "RSA verify time.png")

# Maximum Keygen Memory Usage,
# ,Maximum Encapsulation Memory Usage,,Verification Time Standard Deviation,Maximum Verification Memory Usage,,Public Key length,Secret Key length,Ciphertext length

# DSS THROUGHPUT
fig, ax = plt.subplots(figsize=(20, 10))

throughput_data_orig = data.sort_values(by="Signatures Per Second", ascending=False)
throughput_data_orig = throughput_data_orig.melt(id_vars="index", value_vars=["Signatures Per Second", "Verifications Per Second"])
generate_barplot(throughput_data_orig, "value", None, ("Operations per second", "DSS"), ax, group="variable", legend_title="Metrics")
fig.savefig(RESULTS_FOLDER + "RSA throughput.png")

# KEYGEN
fig, ax = plt.subplots(figsize=(20, 10))

keygen_data_orig = data.sort_values(by="Mean Keygen Time", ascending=True)
keygen_data_orig["Mean Keygen Time"] /= 1_000_000
keygen_data_orig["Keygen Time Standard Deviation"] /= 1_000_000
generate_barplot(keygen_data_orig, "Mean Keygen Time", "Keygen Time Standard Deviation", ('Mean Key Generation CPU Time (ms)', 'DSS'), ax)

fig.savefig(RESULTS_FOLDER + "RSA keygen.png")
