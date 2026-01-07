# SSH Key Permissions Verification

## ✅ Permissions Verified and Correct

**Date:** January 7, 2025  
**Status:** All SSH key permissions are correctly set

## Current Permissions

### Private Key (`~/.ssh/mingus_test`)
- **Current:** `600` (rw-------)
- **Required:** `600` (read/write for owner only)
- **Status:** ✅ **CORRECT**

### Public Key (`~/.ssh/mingus_test.pub`)
- **Current:** `644` (rw-r--r--)
- **Required:** `644` (read/write for owner, read for others)
- **Status:** ✅ **CORRECT**

### SSH Directory (`~/.ssh`)
- **Current:** `700` (drwx------)
- **Required:** `700` (read/write/execute for owner only)
- **Status:** ✅ **CORRECT**

## Permission Details

### Why These Permissions Matter

1. **Private Key (600):**
   - Only the owner can read/write
   - Prevents other users from accessing your private key
   - SSH will refuse to use keys with incorrect permissions

2. **Public Key (644):**
   - Owner can read/write
   - Others can read (needed for sharing with GitHub)
   - Safe to share publicly

3. **SSH Directory (700):**
   - Only the owner can access the directory
   - Protects all SSH keys and configuration files
   - Prevents unauthorized access to SSH files

## Verification Commands

To check permissions at any time:

```bash
# Check private key permissions
ls -l ~/.ssh/mingus_test
# Should show: -rw------- (600)

# Check public key permissions
ls -l ~/.ssh/mingus_test.pub
# Should show: -rw-r--r-- (644)

# Check .ssh directory permissions
ls -ld ~/.ssh
# Should show: drwx------ (700)

# Or use stat for numeric values
stat -f "%A %N" ~/.ssh/mingus_test ~/.ssh/mingus_test.pub ~/.ssh
```

## Setting Permissions (If Needed)

If permissions ever need to be corrected:

```bash
# Set private key permissions
chmod 600 ~/.ssh/mingus_test

# Set public key permissions
chmod 644 ~/.ssh/mingus_test.pub

# Set .ssh directory permissions
chmod 700 ~/.ssh
```

## Security Notes

- ✅ **Never share your private key** (`mingus_test`)
- ✅ **Public key is safe to share** (`mingus_test.pub`)
- ✅ **Keep .ssh directory private** (700 permissions)
- ✅ **SSH will refuse keys with incorrect permissions** (security feature)

## Test Connection

To verify everything works:

```bash
ssh -T github-mingus
```

Expected output:
```
Hi Jahnesta3rd! You've successfully authenticated, but GitHub does not provide shell access.
```

---

**Status:** ✅ **All permissions verified and correct**

