# 🛠️ Roblox Map Builder (Blender to Rojo)

**Roblox Map Builder** is a specialized Blender addon designed to bridge the gap between high-fidelity 3D modeling and the Roblox engine. It enables developers to build 1:1 scale maps in Blender and sync them directly to a **Rojo** project without ever using the Roblox Studio Bulk Importer.

## 🎯 The Goal
The primary objective is to make Blender the "Source of Truth" for Roblox maps. 
- **Automated Pipeline:** Upload FBX models and Textures via Open Cloud APIs directly from the 3D viewport.
- **Rojo Integration:** Generate a `.project.json` file that replicates the Blender hierarchy in Roblox.
- **Shader Parity:** Use a custom "Uber-Shader" in Blender that visually replicates how Roblox handles Part textures (6-face projection) vs. MeshPart textures.

---

## 🚀 Key Features

### 1. Headless MeshId Extraction
Since the Roblox Assets API returns a `Model` ID rather than the underlying `MeshId`, this tool utilizes a clever workaround:
1. **Upload:** Sends the FBX to the Cloud.
2. **Poll:** Wait for the Asset Operation to complete.
3. **Scrape:** Downloads the generated Model file, decompresses it, and uses **Regex** to extract the `rbxassetid://` of the actual Mesh data.
4. **Link:** Renames the Blender Mesh data to `rblx_mesh_{ModelID}_{MeshID}` to ensure persistent tracking and future patching.

### 2. Uber-Shader Material Template
A custom-built node tree is instantiated for every object. This shader includes:
- **Part Mode:** Logic for 6-face texture mapping (Top, Bottom, Front, Back, Left, Right) using UV-space shifting.
- **MeshPart Mode:** Direct texture mapping.
- **Drivers:** Blender properties (`rbx_type`) automatically drive shader nodes (`isMeshPart?`) to change the viewport appearance in real-time.

### 3. Smart Asset Patching
The tool detects if a mesh or texture has already been uploaded. 
- If the name contains an ID, the "Upload" button becomes "Update," triggering a **PATCH** request to the existing cloud asset instead of creating a duplicate.

### 4. 1:1 Scale & Orientation
- **Rotation:** Automatically applies a 180-degree Z-axis offset during export to align Blender's -Y forward with Roblox's -Z forward.
- **Scale:** Handles the conversion between Blender Meters and Roblox Studs using a configurable `FBX_EXPORT_SCALE`.

---

## 📂 Project Architecture

The codebase is refactored into a modular system to prevent "God Script" maintenance issues:

| Module | Responsibility |
| :--- | :--- |
| `api_client.py` | Handles all REST requests (POST/PATCH), Multipart form-data, and Polling logic. |
| `instance_builder.py` | The "Factory" that converts a Blender Object into a Rojo JSON dictionary. |
| `node_builder.py` | Manages the recursive tree traversal, hierarchy, and `WeldConstraint` generation. |
| `material_builder.py` | Reconstructs the complex Uber-Shader node tree from code. |
| `texture_uploader.py` | Scans the shader for new images, uploads them, and renames them to Asset IDs. |
| `export_utils.py` | Safely handles the temporary FBX export and transform zeroing. |
| `math_utils.py` | Handles the Stud conversion and CFrame matrix math. |

---

## 🛠 Installation & Setup

1. **Rojo:** Ensure you have a Rojo project initialized.
2. **API Key:** 
    - Generate an **Open Cloud API Key** on the Roblox Creator Dashboard.
    - Required Permissions: `Assets: Write`, `Assets: Read`.
3. **Preferences:**
    - Paste your API Key and Creator ID (User or Group) into the Addon Preferences in Blender.
4. **Sync:**
    - Set your `Target File` in the Scene Properties (e.g., `//map.project.json`).
    - Click **Sync to Roblox** to generate the hierarchy.

---

## 🗺️ Roadmap

- [x] **Core Model Upload:** FBX to Model asset.
- [x] **MeshId Extraction:** Regex scraping of downloaded assets.
- [x] **Texture Upload:** Automatic renaming of Image objects to `rblx_texture_ID`.
- [x] **Material Parity:** 6-face mapping logic inside Blender.
- [ ] **SurfaceAppearance Support:** Expand the shader to handle PBR (Normal, Roughness, Metalness) for MeshParts.
- [ ] **Instance Spawning:** Support for "Collection Instances" in Blender to export as individual Models with the same MeshId (Memory Optimization).
- [ ] **Headless Studio Verification:** Integration with Luau-Execution API to verify asset placement without opening Studio.

---

## 📄 License
This tool is designed for private/internal development for Roblox Map Builders. Use with care regarding API rate limits.