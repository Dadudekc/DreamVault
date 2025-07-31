# DreamVault Login Instructions

## 🚀 **How to Successfully Login**

### **Step 1: Start the Scraper**
```bash
python run_scraper.py --manual-timeout 600
```

### **Step 2: Browser Window Opens**
- A Chrome browser window will open automatically
- It will navigate to ChatGPT automatically
- Wait for the page to fully load

### **Step 3: Manual Login Process**
1. **Look for the login button** on the ChatGPT page
2. **Click "Log in"** or "Sign in"
3. **Enter your email/username**
4. **Enter your password**
5. **Complete any 2FA** if prompted
6. **Wait for the dashboard to load** (you should see your conversation list)

### **Step 4: Verify Login Success**
- You should see your conversation list on the left side
- The page title should show "ChatGPT" or similar
- You should see conversation titles/links

### **Step 5: Don't Close the Browser**
- **Leave the browser window open**
- The scraper will automatically close it when done
- Do not manually close the browser

## 🔧 **Troubleshooting**

### **If Login Times Out**
- **Check your internet connection**
- **Try refreshing the page** if it doesn't load
- **Make sure you're on the correct ChatGPT site**
- **Try again with a fresh browser session**

### **If You Don't See Login Button**
- **Scroll down** on the page
- **Look for "Log in" or "Sign in"** links
- **Try refreshing the page**

### **If 2FA is Required**
- **Use your authenticator app** (Google Authenticator, Authy, etc.)
- **Enter the 6-digit code** when prompted
- **Wait for verification to complete**

### **If You Get CAPTCHA**
- **Complete the CAPTCHA** if it appears
- **This is normal** for first-time logins
- **Follow the instructions** carefully

## ⏰ **Timing Guidelines**

### **Expected Timeline**
- **Browser opens**: 10-30 seconds
- **Page loads**: 5-15 seconds
- **Manual login**: 30-60 seconds
- **2FA (if needed)**: 15-30 seconds
- **Dashboard loads**: 10-20 seconds

### **Total Time**
- **Typical**: 2-3 minutes total
- **With 2FA**: 3-4 minutes total
- **With CAPTCHA**: 4-5 minutes total

## 🎯 **Success Indicators**

### **✅ Login Successful When:**
- You see your conversation list
- Page title shows "ChatGPT"
- No login prompts remain
- You can see conversation titles

### **❌ Login Failed When:**
- Still seeing login prompts
- Page shows error messages
- No conversation list visible
- Browser closes automatically

## 🚀 **Ready to Extract**

Once login is successful:
- The scraper will automatically start extracting conversations
- You'll see progress updates in the terminal
- All conversations will be saved to `data/raw/`
- The browser will close automatically when complete

---

## 🎯 **Quick Start Command**

```bash
# Start with 10-minute timeout
python run_scraper.py --manual-timeout 600

# Or start with 5-minute timeout for testing
python run_scraper.py --manual-timeout 300 --limit 10
```

**Follow the steps above and your DreamVault will extract all your conversations!** 🚀 