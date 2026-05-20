import urllib.request
url = 'http://localhost:5000/product/5'
html = urllib.request.urlopen(url).read().decode('utf-8', errors='replace')
lines = html.splitlines()
for i in range(1770, 1820):
    line = lines[i]
    if '<script' in line or '</script>' in line:
        print(i+1, line)
