
# what
uses watchdog (fswatch) + orgtools (trivial table parsing) + ftplib to sync (potentially modified versions of) files to a server over ftp. needs a custom html page for each list. why ftp? because i have a cheap server on shared hosting and that's what's available to me.

inspired by https://github.com/mkaz/fswatch/

this is still a hack, but it replaces three previous incarnations that are all much worse hacks:
- upload_org_files.py (previously called by incron on bigpanda)
- post.py (just move files into webmirror insteda)
- lists/*.py (just edit the tables in their files directly)

# how
creates two watchdog observers:
- one to watch my org text directories and process files into something readable by a simple web app, writing to webmirror
- one to watch the webmirror directory and upload via ftp to website

it may not be as good as the ultimate solution of doing everything in org:
- trigger on save
- export to html with template
- template includes js/css
- upload automatically

but it seems like emacs doesn't really handle uploading in a reasonable way, which means i'll end up needing fswatch one way or another. plus i want it to work for any filetype, including stuff i don't edit in emacs. this may be the best solution.


# usage
## osx: 
- `cp net.alanbernstein.fswatch.plist ~/Library/LaunchAgents/.`
- `launchctl load net.alanbernstein.fswatch.plist`
- `launchctl start net.alanbernstein.fswatch`

then, modify the config and the ProcessorHandler methods as necessary
