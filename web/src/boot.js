const params = new URLSearchParams(location.search)
if (params.has('level')) import('./main.js')
else import('./menu.js')