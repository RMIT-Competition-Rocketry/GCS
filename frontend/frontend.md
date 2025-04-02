# Frontend developer documentation

*Developer notes and documentation for working on the GCS frontend.*

Libraries:
- Tailwind
- D3.js

## Tailwind
Tailwind v4.0.17 is used for stylesheets. 

The standalone version of Tailwind will be used so we don't have to rely on node.js. Download it from https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.0.17, rename to `tailwindcss`, and place it in `/third_party/` for development. 

The `/frontend/scripts/` folder has a number of scripts for using Tailwind:

- **tailwind_dev.sh** will update tailwind.css in realtime, as you make changes to the html. Use this while developing the webpage.
- **tailwind_build.sh** will build an optimised and minified version of tailwind.css for production. This probably isn't necessary since it's a fairly small website, but we'll take any optimisations we can get.

## D3.js
D3.js is used for data visualisation.

## Three.js
Three.js is used to render the 3D model of the rocket (extension task).


caspar wuz here!!!!1!
