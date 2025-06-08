import numpy as np
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# Primitive Builders

def create_cube(center, size, color):
    cx, cy, cz = center
    lx, ly, lz = size
    x = [-lx/2, lx/2]
    y = [-ly/2, ly/2]
    z = [-lz/2, lz/2]
    vertices = np.array([[cx+i, cy+j, cz+k] for i in x for j in y for k in z])
    faces = [
        [0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4],
        [2, 3, 7, 6], [1, 3, 7, 5], [0, 2, 6, 4]
    ]
    i, j, k = [], [], []
    for face in faces:
        i += [face[0], face[0], face[2]]
        j += [face[1], face[2], face[3]]
        k += [face[2], face[3], face[0]]

    return go.Mesh3d(x=vertices[:,0], y=vertices[:,1], z=vertices[:,2], i=i, j=j, k=k, color=color)

def create_cylinder(center, radius, height, color, resolution=20):
    cx, cy, cz = center
    theta = np.linspace(0, 2*np.pi, resolution)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z_bottom = np.full_like(theta, cz)
    z_top = np.full_like(theta, cz + height)
    x = np.concatenate([x + cx, x + cx])
    y = np.concatenate([y + cy, y + cy])
    z = np.concatenate([z_bottom, z_top])
    faces = []
    for i in range(resolution):
        next_i = (i + 1) % resolution
        faces.append([i, next_i, resolution + next_i])
        faces.append([i, resolution + next_i, resolution + i])
    i, j, k = zip(*faces)
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color)

def create_sphere(center, radius, color, resolution=20):
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    x = center[0] + radius * np.outer(np.cos(u), np.sin(v)).flatten()
    y = center[1] + radius * np.outer(np.sin(u), np.sin(v)).flatten()
    z = center[2] + radius * np.outer(np.ones_like(u), np.cos(v)).flatten()
    return go.Mesh3d(x=x, y=y, z=z, alphahull=0, color=color)

def create_cone(center, radius, height, color, resolution=20):
    cx, cy, cz = center
    theta = np.linspace(0, 2*np.pi, resolution)
    x = radius * np.cos(theta) + cx
    y = radius * np.sin(theta) + cy
    z = np.full_like(theta, cz)
    x = np.append(x, cx)
    y = np.append(y, cy)
    z = np.append(z, cz + height)
    faces = [[i, (i+1)%resolution, resolution] for i in range(resolution)]
    i, j, k = zip(*faces)
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color)

def create_torus(center, R, r, color, resolution=20):
    cx, cy, cz = center
    theta = np.linspace(0, 2*np.pi, resolution)
    phi = np.linspace(0, 2*np.pi, resolution)
    theta, phi = np.meshgrid(theta, phi)
    x = (R + r * np.cos(phi)) * np.cos(theta) + cx
    y = (R + r * np.cos(phi)) * np.sin(theta) + cy
    z = r * np.sin(phi) + cz
    return go.Surface(x=x, y=y, z=z, colorscale=[[0, color], [1, color]], showscale=False, opacity=1)

# ─────────────────────────────────────────────
# Scene Graph Node

class SceneNode:
    def __init__(self, obj=None, children=None):
        self.obj = obj
        self.children = children or []

    def get_all_objects(self):
        all_objs = []
        if self.obj:
            all_objs.append(self.obj)
        for child in self.children:
            all_objs.extend(child.get_all_objects())
        return all_objs

# ─────────────────────────────────────────────
# Create Table

table = SceneNode()
table.obj = create_cube(center=[0, 0, 1], size=[6, 3, 0.3], color='brown')

# Legs
offsets = [(-2.5, -1), (-2.5, 1), (2.5, -1), (2.5, 1)]
for ox, oy in offsets:
    leg = create_cylinder(center=[ox, oy, 0], radius=0.2, height=1, color='black')
    table.children.append(SceneNode(obj=leg))

# ─────────────────────────────────────────────
# Create Robot di atas meja

robot = SceneNode()

# Body
body = create_cube(center=[0, 0, 1.5], size=[1, 0.6, 1], color='silver')
robot.children.append(SceneNode(body))

# Neck
neck = create_cylinder(center=[0, 0, 2.0], radius=0.1, height=0.2, color='gray')
robot.children.append(SceneNode(neck))

# Head (sphere)
head = create_sphere(center=[0, 0, 2.3], radius=0.3, color='lightblue')
robot.children.append(SceneNode(head))

# Eyes (2 small spheres)
eye_left = create_sphere(center=[-0.1, 0.25, 2.35], radius=0.05, color='black')
eye_right = create_sphere(center=[0.1, 0.25, 2.35], radius=0.05, color='black')
robot.children += [SceneNode(eye_left), SceneNode(eye_right)]

# Antenna (cone)
antenna = create_cone(center=[0, 0, 2.6], radius=0.05, height=0.3, color='white')
robot.children.append(SceneNode(antenna))

# Hands (torus, small at side of body)
# New Hands (Doraemon-style): lengan (balok) + tangan (bola)

# Lengan kiri (lebih dekat ke badan)
arm_left = create_cube(center=[-0.65, 0, 1.75], size=[1, 0.3, 0.25], color='silver')
# Tangan kiri (bola)
hand_left = create_sphere(center=[-1.2, 0, 1.75], radius=0.12, color='white')

# Lengan kanan (lebih dekat ke badan)
arm_right = create_cube(center=[0.65, 0, 1.75], size=[1, 0.3, 0.25], color='silver')
# Tangan kanan (bola)
hand_right = create_sphere(center=[1.2, 0, 1.75], radius=0.12, color='white')


# Tambahkan ke scene robot
robot.children += [SceneNode(arm_left), SceneNode(hand_left),
                   SceneNode(arm_right), SceneNode(hand_right)]

# ─────────────────────────────────────────────
# Final Scene
scene_root = SceneNode(children=[table, robot])
fig = go.Figure(data=scene_root.get_all_objects())
fig.update_layout(scene=dict(aspectmode='data'))

import plotly.io as pio

html_str = pio.to_html(fig, full_html=True, include_plotlyjs='cdn')

with open("index.html", "w") as f:
    f.write(html_str)

fig.show()
