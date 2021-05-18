import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import oqs

CSVs_TO_OPEN = [
    "oqs_bench/testing/results/pi/sign/CRYSTALS-DILITHIUM.csv",
    "oqs_bench/testing/results/pi/sign/FALCON.csv",
    "oqs_bench/testing/results/pi/sign/Picnic.csv",
    "oqs_bench/testing/results/pi/sign/Rainbow.csv",
    "oqs_bench/testing/results/pi/sign/SPHINCS+.csv",
]
RESULTS_FOLDER = "visualizations/pi/sign/"

# Load data to pandas
frames = []
for _file in CSVs_TO_OPEN:
    frames.append(pd.read_csv(_file, index_col=0))
data = pd.concat(frames).reset_index()
print(data.head())

# Get Claimed NIST level
def get_nist_level(sign):
    with oqs.Signature(sign) as client:
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

# DSS Encryption
fig, ax = plt.subplots(len(data["Claimed NIST Level"].unique()), figsize=(20, 30))

encrypt_timing_data = data.sort_values(by="Mean Encapsulation Time")
encrypt_timing_data["Mean Encapsulation Time"] /= 1_000_000
encrypt_timing_data["Encapsulation Time Standard Deviation"] /= 1_000_000
for i, level in enumerate(sorted(data["Claimed NIST Level"].unique())):
    encrypt_timing_data_sub = encrypt_timing_data[encrypt_timing_data["Claimed NIST Level"] == level]
    generate_barplot(encrypt_timing_data_sub, "Mean Encapsulation Time", "Encapsulation Time Standard Deviation", ('Mean Signing CPU Time (ms)', 'DSS'), ax[i])
    ax[i].title.set_text(f"NIST Level {level}")

fig.savefig(RESULTS_FOLDER + "sign time.png")

# DSS Decryption
fig, ax = plt.subplots(len(data["Claimed NIST Level"].unique()), figsize=(20, 30))

decrypt_timing_data = data.sort_values(by="Mean Verification Time")
decrypt_timing_data["Mean Verification Time"] /= 1_000_000
decrypt_timing_data["Verification Time Standard Deviation"] /= 1_000_000
for i, level in enumerate(sorted(data["Claimed NIST Level"].unique())):
    decrypt_timing_data_sub = decrypt_timing_data[decrypt_timing_data["Claimed NIST Level"] == level]
    generate_barplot(decrypt_timing_data_sub, "Mean Verification Time", "Verification Time Standard Deviation", ('Mean Verification CPU Time (ms)', 'DSS'), ax[i])
    ax[i].title.set_text(f"NIST Level {level}")

fig.savefig(RESULTS_FOLDER + "verify time.png")

# Maximum Keygen Memory Usage,
# ,Maximum Encapsulation Memory Usage,,Verification Time Standard Deviation,Maximum Verification Memory Usage,,Public Key length,Secret Key length,Ciphertext length

# DSS THROUGHPUT
fig, ax = plt.subplots(len(data["Claimed NIST Level"].unique()), figsize=(20, 30))

throughput_data_orig = data.sort_values(by="Signatures Per Second", ascending=False)
for i, level in enumerate(sorted(data["Claimed NIST Level"].unique())):
    throughput_data = throughput_data_orig[throughput_data_orig["Claimed NIST Level"] == level]
    throughput_data = throughput_data.melt(id_vars="index", value_vars=["Signatures Per Second", "Verifications Per Second"])
    generate_barplot(throughput_data, "value", None, ("Operations per second", "DSS"), ax[i], group="variable", legend_title="Metrics")
    ax[i].title.set_text(f"NIST Level {level}")

fig.savefig(RESULTS_FOLDER + "throughput.png")

# KEYGEN
fig, ax = plt.subplots(len(data["Claimed NIST Level"].unique()), figsize=(20, 30))

keygen_data_orig = data.sort_values(by="Mean Keygen Time", ascending=True)
keygen_data_orig["Mean Keygen Time"] /= 1_000_000
keygen_data_orig["Keygen Time Standard Deviation"] /= 1_000_000
for i, level in enumerate(sorted(data["Claimed NIST Level"].unique())):
    keygen_time_data = keygen_data_orig[keygen_data_orig["Claimed NIST Level"] == level]
    generate_barplot(keygen_time_data, "Mean Keygen Time", "Keygen Time Standard Deviation", ('Mean Key Generation CPU Time (ms)', 'DSS'), ax[i])
    ax[i].title.set_text(f"NIST Level {level}")

fig.savefig(RESULTS_FOLDER + "keygen.png")
