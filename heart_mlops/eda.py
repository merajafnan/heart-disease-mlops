"""Create reproducible exploratory data analysis charts."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from heart_mlops.config import FIGURE_DIR, NUMERIC_FEATURES, TARGET
from heart_mlops.data import prepare_data


def run_eda():
    data, summary = prepare_data()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")

    ax = sns.countplot(data=data, x=TARGET, hue=TARGET, legend=False)
    ax.set(xlabel="Heart disease present", ylabel="Patient count", title="Class balance")
    ax.set_xticks([0, 1], ["No", "Yes"])
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "class_balance.png", dpi=160)
    plt.close()

    axes = data[NUMERIC_FEATURES].hist(figsize=(10, 7), bins=20)
    axes[0, 0].figure.suptitle("Numeric feature distributions")
    axes[0, 0].figure.tight_layout()
    axes[0, 0].figure.savefig(FIGURE_DIR / "numeric_histograms.png", dpi=160)
    plt.close(axes[0, 0].figure)

    plt.figure(figsize=(9, 7))
    sns.heatmap(data.corr(numeric_only=True), cmap="coolwarm", center=0, vmin=-1, vmax=1)
    plt.title("Feature and target correlations")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "correlation_heatmap.png", dpi=160)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    sns.boxplot(data=data, x=TARGET, y="age", ax=axes[0])
    sns.boxplot(data=data, x=TARGET, y="thalach", ax=axes[1])
    for ax in axes:
        ax.set_xticks([0, 1], ["No", "Yes"])
        ax.set_xlabel("Heart disease present")
    axes[0].set_title("Age by target")
    axes[1].set_title("Maximum heart rate by target")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "feature_by_target.png", dpi=160)
    plt.close(fig)

    (FIGURE_DIR / "eda_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved four charts to {FIGURE_DIR}")


if __name__ == "__main__":
    run_eda()

