property repoPath : "/Users/sa/rh.1"

on run
	repeat
		set choice to button returned of (display dialog "Rhea Control Panel (AppleScript)\nChoose an action:" buttons {"Status", "Wake REX", "Drain GPT", "Drain LEAD", "Drain REX", "Restart Watcher", "Open Pulse UI", "Quit"} default button "Status" cancel button "Quit" with title "Rhea Panel")
		
		if choice is "Quit" then exit repeat
		
		if choice is "Status" then
			my runCmd("python3 ops/rex_pager.py status | sed -n '1,120p'", "Relay Status")
		else if choice is "Wake REX" then
			my runCmd("python3 ops/rex_pager.py wake REX", "Wake REX")
		else if choice is "Drain GPT" then
			my runCmd("python3 ops/rex_pager.py drain GPT", "Drain GPT")
		else if choice is "Drain LEAD" then
			my runCmd("python3 ops/rex_pager.py drain LEAD", "Drain LEAD")
		else if choice is "Drain REX" then
			my runCmd("python3 ops/rex_pager.py drain REX", "Drain REX")
		else if choice is "Restart Watcher" then
			my runCmd("pkill -f \"ops/rex_pager.py watch --interval 5\" || true; nohup python3 ops/rex_pager.py watch --interval 5 >/tmp/rex_watch.log 2>&1 & sleep 1; pgrep -af \"ops/rex_pager.py watch --interval 5\" | sed -n '1,5p'", "Restart Watcher")
		else if choice is "Open Pulse UI" then
			my openPulseUI()
		end if
	end repeat
end run

on runCmd(innerCmd, dialogTitle)
	try
		set fullCmd to "/bin/zsh -lc " & quoted form of ("cd " & quoted form of repoPath & " && " & innerCmd & " 2>&1")
		set outputText to do shell script fullCmd
		if outputText is "" then set outputText to "OK"
		display dialog my truncateText(outputText, 3000) buttons {"Back"} default button "Back" with title dialogTitle
	on error errMsg number errNum
		display dialog "ERROR [" & errNum & "]: " & errMsg buttons {"Back"} default button "Back" with title dialogTitle
	end try
end runCmd

on openPulseUI()
	tell application "Terminal"
		activate
		do script "cd " & quoted form of repoPath & " && python3 ops/virtual-office/pulse_buttons.py"
	end tell
	display dialog "Pulse UI launched in Terminal." buttons {"Back"} default button "Back" with title "Open Pulse UI"
end openPulseUI

on truncateText(t, maxLen)
	if (length of t) ≤ maxLen then return t
	return text 1 thru maxLen of t & return & "..." & return & "(output truncated)"
end truncateText
