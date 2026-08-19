import re

path = "robot_sim.urdf"
with open(path) as f:
    urdf = f.read()

# joint名: (lower_rad, upper_rad)  ※測定度→ラジアン、Y〜360は Y-360〜0 に読替
limits = {
    "LR_HAA": (0.0,     0.716),
    "LL_HAA": (0.297,   1.082),
    "LR_HR":  (-2.688,  0.859),
    "LL_HR":  (-1.431,  1.850),
    "LR_HFE": (-1.047,  2.443),
    "LL_HFE": (2.269,   5.585),
    "LR_KFE": (-1.885,  0.796),
    "LL_KFE": (-1.012,  2.059),
    "LR_FFE": (-1.885, -0.017),
    "LL_FFE": (1.073,   3.203),
}
EFFORT = 18.0
VELOCITY = 20.0

def repl(m):
    name = m.group("name")
    block = m.group(0)
    if name not in limits:
        return block
    lo, hi = limits[name]
    new_limit = f'<limit effort="{EFFORT}" velocity="{VELOCITY}" lower="{lo}" upper="{hi}"/>'
    if "<limit" in block:
        block = re.sub(r'<limit[^/]*/>', new_limit, block)
    else:
        block = block.replace("</joint>", "  " + new_limit + "\n  </joint>")
    return block

pattern = re.compile(r'<joint name="(?P<name>[^"]+)" type="revolute">.*?</joint>', re.DOTALL)
urdf = pattern.sub(repl, urdf)

with open(path, "w") as f:
    f.write(urdf)
print("done")
