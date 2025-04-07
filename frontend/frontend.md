# Frontend developer documentation

*Developer notes and documentation for working on the GCS frontend.*



## Libraries
We're using the following libraries for frontend:
- Tailwind v4.0.17
- D3.js v7.9.0
- Three.js v0.175.0

All of these libraries have been included as standalone JS so we don't have to rely on NPM or a CDN. 

Unless updating them is absolutely necessary, we will be using these specific versions throughout the capstone project. Updating in the middle of development can add a lot of work and cause weird glitches.

### Tailwind
**Tailwind v4.0.17 is used for stylesheets.**

The standalone version of Tailwind will be used so we don't have to rely on node.js. Download it from https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.0.17, rename to *tailwindcss*, and place it INSIDE `/third_party/` for development. 

The `/frontend/scripts/` folder has a number of scripts for using Tailwind:

- *tailwind_dev.sh* will update tailwind.css in realtime, as you make changes to the html. Use this while developing the webpage.
- *tailwind_build.sh* will build an optimised and minified version of tailwind.css for production. This probably isn't necessary since it's a fairly small website, but we'll take any optimisations we can get.

#### **Windows Instructions**

Make sure to unblock the executable in explorer by **right clicking > properties > unblock**. You'll also need to make sure the file is named *tailwindcss.exe*.

In order to run either of the scripts in VS Code, on the toolbar click **Terminal > New Task > [any of the tailwind scripts] > Continue without scanning task output**

If you're not using VS Code, you can try running *tailwind_dev.bat* and *tailwind_build.bat* by opening a new terminal and typing `frontend\scripts\tailwind_dev.bat` or `frontend\scripts\tailwind_build.bat` from the repository root.

### D3.js
**D3.js v7.9.0 is used for data visualisation.**

It lets us make pretty graphs

### Three.js
**Three.js v0.175.0 is used to render the 3D model of the rocket.**

Included with this is the **GLTFLoader.js** loader, which lets us load .gltf and .glb model files.

## Old GUI
The old interface has been included as developer reference, including the CSS. These files shouldn't be used for our frontend, but they're a good starting point for understanding what might be expected in our interface.

The following files are part of the old GUI:
- /oldgui.html
- /css/bootstrap.css
- /css/oldgui.css