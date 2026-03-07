# BlenderMap Integration Setup

This project uses **Rojo** to sync external assets and map data from your file system into Roblox Studio. Follow these steps to get the environment running.

## Prerequisites

1.  **Rojo CLI**: Ensure you have the Rojo CLI installed (v7.0 or later recommended). You can install it via [rojo.space](https://rojo.space/docs/v7/installation/).
2.  **Rojo Studio Plugin**: Install the Rojo plugin in Roblox Studio from the [Roblox Marketplace](https://www.roblox.com/library/2911631885/Rojo-7).
3.  **VS Code (Optional)**: Highly recommended for managing the project structure.

## Setup Instructions

### 1. Clone the Repository
Clone this project to your local machine:
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Configure the Project JSON (Crucial)
This project is structured as a sub-project. You must tell your main Rojo configuration where the `BlenderMap` project lives. 

Open your `default.project.json` file in the root of your project and add the `BlenderMap` entry under the **Workspace** properties as shown below:

```json
"Workspace": {
  "$properties": {
    "FilteringEnabled": true
  },
  "BlenderMap": {
    "$path": "src/world/BlenderMap.project.json"
  }
}
```

> **Note:** Ensure the path `"src/world/BlenderMap.project.json"` correctly points to the location of the map project file included in this repository.

### 3. Start the Rojo Server
Run the following command in your terminal to start syncing:
```bash
rojo serve
```

### 4. Connect to Roblox Studio
1.  Open your desired `.rbxl` file or a new place in **Roblox Studio**.
2.  Navigate to the **Plugins** tab.
3.  Open the **Rojo** menu and click **Connect**.
4.  You should see the `BlenderMap` folder populate inside the `Workspace` automatically.

## Troubleshooting
*   **Path Errors**: If Rojo fails to serve, double-check that the `$path` in your `default.project.json` matches your local folder structure exactly.
*   **Port Conflicts**: If port `6005` is in use, you may need to specify a different port in the serve command (`rojo serve --port 6006`).
