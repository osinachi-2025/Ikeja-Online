import urllib.request
url='http://localhost:5000/product/2'
html=urllib.request.urlopen(url).read().decode('utf-8', errors='replace')
for term in ['function openAuth','function closeAuth','function openWishlist','function openDrawer','function showProfile']:
    print(term, 'FOUND' if term in html else 'MISSING')
print('script-start', html.find('<script src="/static/js/wishlist-system.js"></script>'))
print('openAuth-pos', html.find('function openAuth'))
print('openWishlist-pos', html.find('function openWishlist'))
print('script-close', html.rfind('</script>'))
