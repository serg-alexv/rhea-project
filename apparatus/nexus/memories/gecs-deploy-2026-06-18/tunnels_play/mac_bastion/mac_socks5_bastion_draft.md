# Mac SOCKS5 Bastion for Clean US IP (Google Workspace Trial Signup)
# Artifact FYI - not a task. Draft shared for learning/ingestion into rhea memory.

## Step 1. Raise SOCKS5 bastion on Mac
# Open regular Terminal on Mac (not SSH to router) and run dynamic port forward to your VM instance-20260607-122150 (IP 136.114.55.151, account timelabs_ad):

ssh -D 1080 timelabs_ad@136.114.55.151 -o StrictHostKeyChecking=no

# (Leave this Terminal window open. Now your Mac has a personal US proxy gateway on port 1080, connected directly to the heart of Google).

## Step 2. Launch isolated Safari through the Bastion
# To avoid breaking system settings for the entire OS, we tell Safari to go to the network strictly through our SOCKS5 gateway.

# On Mac go to:
# System Settings -> Network -> Wi-Fi -> Details -> Proxies
# Enable the SOCKS Proxy toggle.
# Enter:
# Server: 127.0.0.1
# Port: 1080
# Click OK and Apply.

## Step 3. Grab the 30-day trial via the direct clean link
# Now return to your private Safari window.
# The link you were entering was broken.
# Paste the absolutely clean, default registration address, without reseller tails:

https://google.com

# This page will load instantly because traffic flies from the Iowa datacenter with zero delay.
# The form will come alive because the traffic is coming from the Iowa datacenter without a single delay.
# Enter the domain blueshoeses.com and grab Business Standard along with Gemini Enterprise!

# Notes from context:
# - This complements router-based clean IP (blueshoes WiFi + Passwall2/sing-box/Xray to 35.224.79.36 or other gcloud).
# - Mac was "нормик" after nuking foreign VPN apps; this forces clean IP for browser signup.
# - For phone: still the router Xray SOCKS or transparent path (phone_clean_ip_fix.sh).
# - Domain: LeoTimelabs (Porkbun) for verification if needed.
# - After signup: add users, verify domain via clean path to keep fraud low.
