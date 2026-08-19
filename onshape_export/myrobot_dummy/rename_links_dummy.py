import re

path = "robot_sim.urdf"
with open(path) as f:
    urdf = f.read()

# 長い名前から順に置換（part_1 が part_1_2 の一部に誤マッチするのを防ぐ）
mapping = [
    ("part_1_11", "ll_ffe"),
    ("part_1_10", "ll_kfe"),
    ("part_1_9",  "ll_hfe"),
    ("part_1_8",  "ll_haa"),
    ("part_1_7",  "ll_hr"),
    ("part_1_6",  "lr_hr"),
    ("part_1_5",  "lr_ffe"),
    ("part_1_4",  "lr_kfe"),
    ("part_1_3",  "lr_hfe"),
    ("part_1_2",  "lr_haa"),
    ("part_1",    "base"),
]

# link name= と parent/child link= のみ置換（filename= は対象外）
for old, new in mapping:
    urdf = re.sub(r'(<link name=")' + old + r'(")', r'\g<1>' + new + r'\g<2>', urdf)
    urdf = re.sub(r'(<parent link=")' + old + r'(")', r'\g<1>' + new + r'\g<2>', urdf)
    urdf = re.sub(r'(<child link=")' + old + r'(")', r'\g<1>' + new + r'\g<2>', urdf)

with open(path, "w") as f:
    f.write(urdf)

print("done")
