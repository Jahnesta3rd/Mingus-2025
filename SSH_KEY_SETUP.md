# SSH Key Setup for Mingus Testing

## ✅ SSH Key Created Successfully

**Key Details:**
- **Key Type:** ED25519
- **Comment:** mingus-test-environment
- **Private Key:** `~/.ssh/mingus_test`
- **Public Key:** `~/.ssh/mingus_test.pub`
- **Fingerprint:** `SHA256:i9wWyqky8Wp/26oAAZG7RW91meMEPSNcXuQfRvyqDO8`

## Next Steps

### Step 1: Copy Your Public Key

Your public key is displayed above. Copy the entire key (it starts with `ssh-ed25519` and ends with `mingus-test-environment`).

### Step 2: Add SSH Key to GitHub

1. Go to GitHub.com and sign in
2. Click your profile picture → **Settings**
3. Scroll down to **SSH and GPG keys** (left sidebar)
4. Click **New SSH key**
5. Fill in the form:
   - **Title:** `Mingus Test Environment` (or any descriptive name)
   - **Key type:** Authentication Key
   - **Key:** Paste your public key (the entire `ssh-ed25519...` line)
6. Click **Add SSH key**

### Step 3: Test SSH Connection

Test the connection to GitHub:

```bash
ssh -T -i ~/.ssh/mingus_test git@github.com
```

You should see:
```
Hi Jahnesta3rd! You've successfully authenticated, but GitHub does not provide shell access.
```

### Step 4: Configure Git to Use This Key

#### Option A: Use SSH URL with Specific Key (Recommended for Testing)

When pushing, specify the key:

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/mingus_test" git push git@github.com:Jahnesta3rd/Mingus-2025.git main
```

#### Option B: Configure SSH Config (Recommended for Permanent Use)

Create or edit `~/.ssh/config`:

```bash
# Add this to ~/.ssh/config
Host github-mingus
    HostName github.com
    User git
    IdentityFile ~/.ssh/mingus_test
    IdentitiesOnly yes
```

Then use this host for your remote:

```bash
git remote set-url origin git@github-mingus:Jahnesta3rd/Mingus-2025.git
```

#### Option C: Use as Default Key (If this is your only GitHub key)

If this is your primary GitHub key, you can add it to your SSH agent:

```bash
# Start SSH agent
eval "$(ssh-agent -s)"

# Add your key
ssh-add ~/.ssh/mingus_test

# Test connection
ssh -T git@github.com
```

## Security Notes

- ✅ **Private key** (`~/.ssh/mingus_test`) should **NEVER** be shared or committed to git
- ✅ **Public key** (`~/.ssh/mingus_test.pub`) is safe to share and add to GitHub
- ✅ Keep your private key secure with proper file permissions (should be `600`)
- ✅ If you set a passphrase, you'll need to enter it when using the key (or use `ssh-agent`)

## File Permissions

Ensure your SSH key has the correct permissions:

```bash
chmod 600 ~/.ssh/mingus_test
chmod 644 ~/.ssh/mingus_test.pub
chmod 700 ~/.ssh
```

## Troubleshooting

### If SSH connection fails:
1. Verify the public key was added correctly to GitHub
2. Check that you're using the correct key: `ssh -T -i ~/.ssh/mingus_test git@github.com`
3. Ensure file permissions are correct (see above)

### If git push fails:
1. Verify your remote URL: `git remote -v`
2. Make sure you're using the SSH URL: `git@github.com:Jahnesta3rd/Mingus-2025.git`
3. Test SSH connection first (Step 3 above)

---

**Status:** ✅ SSH key created and ready to add to GitHub

