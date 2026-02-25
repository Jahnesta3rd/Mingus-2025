# Why test.mingusapp.com still gets mingusapp.com cert

Run these **on the server** (ssh test.mingusapp.com) to see why the wrong cert is used.

## 1. What is in sites-enabled?

```bash
ls -la /etc/nginx/sites-enabled/
```

If you see **default** or any file besides **mingusapp.com**, that file may define a `listen 443 ssl` (or `default_server`) and take precedence.

## 2. Which 443 server blocks does nginx load?

```bash
sudo nginx -T 2>/dev/null | grep -E "listen 443|server_name|ssl_certificate " | head -40
```

Look for the **first** `listen 443` and its `ssl_certificate` and `server_name`. If the first 443 block uses mingusapp.com cert, that block is the default for 443.

## 3. What does the loaded mingusapp.com config look like?

```bash
grep -n "server_name\|listen 443\|ssl_certificate " /etc/nginx/sites-available/mingusapp.com | head -30
```

Confirm the **first** `listen 443` block has `server_name test.mingusapp.com` and `ssl_certificate .../test.mingusapp.com/...`.

## 4. Fix: make test the explicit default for 443

If another file (e.g. default) or include order makes production the default 443 server, add **default_server** to the **test** HTTPS block so nginx uses it when no other server_name matches. Then only the test block will handle 443 unless SNI matches production.

On the server, edit the config:

```bash
sudo nano /etc/nginx/sites-available/mingusapp.com
```

Find the **test** HTTPS server block (the one with `server_name test.mingusapp.com` and `ssl_certificate .../test.mingusapp.com/...`). Change:

```nginx
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name test.mingusapp.com;
```

to:

```nginx
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    server_name test.mingusapp.com;
```

Save, then:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**Warning:** That makes test.mingusapp.com the **default** for all HTTPS connections that don’t match another server_name (e.g. by IP or unknown host). If this server only serves test and production with correct hostnames, that’s usually fine. If you have other HTTPS vhosts, don’t add default_server and instead fix the other config so only mingusapp.com defines these two hosts.

Then verify again:

```bash
echo | openssl s_client -connect test.mingusapp.com:443 -servername test.mingusapp.com 2>/dev/null | openssl x509 -noout -subject
```

You should see `subject=CN = test.mingusapp.com`.
