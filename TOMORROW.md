# TOMORROW — the whole day. Ignore every other file.

## 8:40am — one command

    pythia
    python3 scripts/morning.py

It checks the account, thinks about the market, and explains in plain English
what it found. It does NOT place any orders. Read it.

## Then, if the numbers look sane

    python3 run.py --loop

Leave that window open. That is the robot trading. Go about your day.
To stop it: click that window, press Control-C.
To halt instantly from anywhere: `touch ~/Downloads/pythia/KILL`

## Sometime before 3pm — post once

The morning command prints your post text AND the exact command to make the
image. Copy the image command, run it, then paste the text into X with the
image attached. Reply to your pinned post so the thread grows.

## 3:05pm — the letter (optional but good)

    python3 run.py --letter

Claude writes the day's fund letter from the journal. Post it. Done.

## That is the entire day. Everything else this week is the same day again.

Wednesday: record a 2-minute screen video (Cmd+Shift+5) reading the script
in PLAYBOOK.md while clicking around the dashboard.
Thursday: fill your numbers into WRITEUP.md, submit on lablab.
Friday 10:00am CT: deadline. Post the final number, win or lose.
