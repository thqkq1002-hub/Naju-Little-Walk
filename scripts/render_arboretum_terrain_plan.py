"""Render the saved research samples with matplotlib; no network or model edits.

Install matplotlib in work/terrain-analysis-libs or use an existing installation.
The map colours and profile are DSM surface samples, not surveyed ground heights.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCAL_LIBS = ROOT / "work/terrain-analysis-libs"
if LOCAL_LIBS.exists():
    sys.path.insert(0, str(LOCAL_LIBS))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "work/terrain-analysis-mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.path import Path as PlotPath
import numpy as np
from PIL import Image

SOURCE = ROOT / "knowledge/sources/arboretum/terrain-analysis-2026-10-03"
OUT = ROOT / "outputs/arboretum-terrain-plan-2026-10-03"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("C:/Windows/Fonts/malgun.ttf")
if FONT.exists():
    font_manager.fontManager.addfont(str(FONT))
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(FONT)).get_name()
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 11,
    "axes.titleweight": "bold", "axes.edgecolor": "#b3bfb9",
    "figure.facecolor": "#f6f5ef", "savefig.facecolor": "#f6f5ef"})


def read(name):
    return json.loads((SOURCE / name).read_text(encoding="utf-8"))


analysis = read("analysis.json")
regional = read("regional-glo90.json")
campus = read("campus-glo90.json")
satellite = read("regional-satellite.json")
geometry = json.loads((ROOT / "knowledge/sources/arboretum/geometry.json").read_text(encoding="utf-8"))
polygon = np.array(analysis["campusPolygon"])
profile = analysis["avenueSurfaceProfile"]["samples"]
avenue = np.array([[s["x"], -s["z"]] for s in profile])
origin_lat, origin_lon = regional["originWGS84"]
lon_scale = 111320*math.cos(math.radians(origin_lat))


def mercator_local(mx, my):
    lon = math.degrees(mx/6378137)
    lat = math.degrees(2*math.atan(math.exp(my/6378137))-math.pi/2)
    return ((lon-origin_lon)*lon_scale, (lat-origin_lat)*111320)


extent = satellite["response"]["extent"]
xmin, north_min = mercator_local(extent["xmin"], extent["ymin"])
xmax, north_max = mercator_local(extent["xmax"], extent["ymax"])
fig = plt.figure(figsize=(15.5, 11), layout="constrained")
layout = fig.add_gridspec(3, 2, height_ratios=[3.6, 1.6, .46])
left = fig.add_subplot(layout[0, 0])
right = fig.add_subplot(layout[0, 1])
bottom = fig.add_subplot(layout[1, :])
footer = fig.add_subplot(layout[2, :])
fig.suptitle("나주수목원 지형 분석 · 평면 정원을 산기슭 경관으로", fontsize=21,
             color="#153e32", x=.04, ha="left")
left.imshow(Image.open(SOURCE / "regional-satellite.jpg"),
    extent=[xmin, xmax, north_min, north_max], origin="upper")
left.set_title("1  위성영상 + 현재 모델 범위", loc="left", pad=12)

grid = analysis["regionalGrid"]
xs = np.array(grid["xs"])
norths = -np.array(grid["zs"])
height = np.array([s["elevationMetres"] for s in regional["samples"]]).reshape(len(norths), len(xs))
cmap = colors.LinearSegmentedColormap.from_list("arboretum_surface",
    ["#e7ead3", "#a9c090", "#5b8662", "#907251", "#c8ad86"])
# A coarse raster is intentionally shown without interpolated fine contours.
mesh = right.pcolormesh(xs, norths, height, shading="nearest", cmap=cmap,
                       vmin=25, vmax=260, rasterized=True)
right.scatter([s["x"] for s in regional["samples"]],
              [-s["z"] for s in regional["samples"]], s=9, color="#344b3b", alpha=.65)
right.set_title("2  고도 표본 · 넓은 범위 250m 간격", loc="left", pad=12)
colorbar = fig.colorbar(mesh, ax=right, shrink=.84, pad=.015)
colorbar.set_label("DSM 표면 고도 (m)")

for ax in (left, right):
    ax.add_patch(Polygon(np.column_stack((polygon[:, 0], -polygon[:, 1])),
                        closed=True, fill=False, edgecolor="#fff4a1", linewidth=2.4, zorder=5))
    ax.plot(avenue[:, 0], avenue[:, 1], color="#ffae5c", linewidth=3, zorder=6)
    ax.scatter(avenue[0, 0], avenue[0, 1], s=52, color="#fff", edgecolor="#293e35", zorder=7)
    ax.set_xlim(-650, 1080)
    ax.set_ylim(-500, 650)
    ax.set_aspect("equal")
    ax.set_xlabel("동쪽 → (현재 프로젝트 좌표, m)")
    ax.set_ylabel("북쪽 → (m)")
    ax.annotate("N", xy=(.94, .93), xytext=(.94, .78), xycoords="axes fraction",
        textcoords="axes fraction", ha="center", color="#fff" if ax is left else "#153e32",
        fontweight="bold", arrowprops={"arrowstyle": "-|>", "color": "#fff" if ax is left else "#153e32"})

label_box = dict(boxstyle="round,pad=.45", facecolor="#f6f5ef", edgecolor="none", alpha=.94)
left.annotate("A  정원·가로수길\n완만한 오르막 반영", xy=(-290, 0), xytext=(-610, 380),
              bbox=label_box, color="#153e32", arrowprops={"arrowstyle": "->", "color": "#fff", "lw": 1.6})
left.annotate("B  산기슭 연결부\n숲길 위치·높이 추가 확인", xy=(80, -15), xytext=(300, 350),
              bbox=label_box, color="#153e32", arrowprops={"arrowstyle": "->", "color": "#fff", "lw": 1.6})
left.annotate("C  동·남동쪽 산지\n먼 경관과 근거리 숲길 구분", xy=(500, -250), xytext=(-580, -390),
              bbox=label_box, color="#153e32", arrowprops={"arrowstyle": "->", "color": "#fff", "lw": 1.6})
left.legend(handles=[Line2D([0], [0], color="#fff4a1", lw=2, label="현재 모델의 OSM 지면 경계"),
                     Line2D([0], [0], color="#ffae5c", lw=3, label="기존 모델의 메타세쿼이아길 축")],
            loc="lower right", framealpha=.95, fontsize=9)

campus_path = PlotPath(polygon)
for s in campus["samples"]:
    if "row" in s and campus_path.contains_point((s["x"], s["z"])):
        right.scatter(s["x"], -s["z"], s=17, facecolors="none", edgecolors="#fff", linewidths=.7, zorder=7)
right.text(.035, .955, "경계 안: 90m 간격 29점, 표면값 39–79m\n입구 약 40m → 기존 길 안쪽 끝 약 65m",
           transform=right.transAxes, va="top", fontsize=10, bbox=label_box, color="#153e32")

distances = [math.hypot(s["x"]-profile[0]["x"], s["z"]-profile[0]["z"]) for s in profile]
values = [s["elevationMetres"] for s in profile]
bottom.plot(distances, values, color="#32624a", marker="o", linewidth=2.2,
            label="DSM 표본을 잇는 선 (최종 노면 높이 아님)")
bottom.axhline(values[0], color="#818a85", linestyle="--", linewidth=1,
               label="현재 모델: 지면 높이 0m의 평면 (비교용 기준 이동)")
bottom.fill_between(distances, values[0], values, color="#a9c090", alpha=.35)
for i in (0, 5, 10):
    bottom.annotate(f"{values[i]:.0f}m", (distances[i], values[i]), xytext=(0, 9),
                    textcoords="offset points", ha="center", color="#153e32", fontsize=10)
bottom.set_ylim(37, 71)
bottom.set_xlim(-10, 440)
bottom.set_xticks([0, 100, 200, 300, 400])
bottom.set_xlabel("기존 메타세쿼이아길 축을 따라 이동한 거리 (m)")
bottom.set_ylabel("DSM 표면값 (m)")
bottom.set_title("3  기존 길 약 430m의 예비 단면 · 표본 양끝 높이차 +25m", loc="left", pad=10)
bottom.grid(axis="y", alpha=.2)
bottom.legend(loc="upper left", fontsize=9, framealpha=.9)

footer.axis("off")
footer.text(0, .95,
    "읽는 법: 산지의 방향·높이차를 확인하는 예비 분석입니다. 90m 원자료에는 수관·건물 높이가 섞일 수 있습니다.\n"
    "점 사이 선과 색상은 설명용이며 실측 등고선이 아닙니다. 위성 촬영일 미확인 · 공식 안내도는 지오리퍼런싱 전 단계.\n"
    "출처: Copernicus GLO-90 / Open-Meteo · Esri, Vantor, Earthstar Geographics, GIS User Community · OSM contributors / ODbL\n"
    "자료 조회 2026-10-03 · A/B/C는 제작 범위를 설명하는 구분이며 공식 시설 구역선이 아닙니다.",
    va="top", fontsize=9, color="#4c5d53", linespacing=1.65)
fig.savefig(OUT / "terrain-analysis.png", dpi=150)
fig.savefig(OUT / "terrain-analysis.pdf")
plt.close(fig)
print(str(OUT / "terrain-analysis.png"))
