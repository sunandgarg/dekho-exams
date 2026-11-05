from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

figure, axes = plt.subplots(figsize=(6, 3.5), constrained_layout=True)
try:
    axes.bar(["DEL", "BOM", "BLR"], [375, 250, 175], color="#286c83", width=0.6)
    axes.set(title="Accepted receipts by region", ylabel="Amount (minor units)")
    axes.set_ylim(bottom=0)
    axes.spines[["top", "right"]].set_visible(False)
    with BytesIO() as output:
        figure.savefig(output, format="png", dpi=120)
        image = output.getvalue()
    print("PNG container:", image.startswith(b"\x89PNG\r\n\x1a\n"))
finally:
    plt.close(figure)
print("open figures:", len(plt.get_fignums()))
