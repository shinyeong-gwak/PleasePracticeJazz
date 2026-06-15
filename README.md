│  app.py
│  navigation.py
│  README.md
│  requirements.txt
│
├─data
│  └─music
│          playlist.py
│          playlists.json
│          sync_logs.json
│
├─downloads
│  ├─licks
│  │      Ugetsu-lick-1.mp3
│  │      Ugetsu-lick-2.mp3
│  │      Ugetsu-pitch-1.mp3
│  │
│  └─mp3
│          This I Dig Of You (Remastered 1999⧸Rudy Van Gelder Edition).mp3
│          Ugetsu.mp3
│
├─lib
│  └─ffmpeg
│      │  LICENSE.txt
│      │
│      └─ bin
│           avcodec-62.dll
│           avdevice-62.dll
│           avfilter-11.dll
│           avformat-62.dll
│           avutil-60.dll
│           ffmpeg.exe
│           ffplay.exe
│           ffprobe.exe
│           swresample-6.dll
│           swscale-9.dll
├─pages
├─repositories
│  │  clip_repository.py
│  │  lick_repository.py
│  │  music_log_repository.py
│  │  playlist_repository.py
│  └─ __init__.py
│
├─routers
│  └─ audio_router.py
├─services
│  │  audio_service.py
│  │  clip_service.py
│  │  music_service.py
│  └─ __init__.py
│
│
├─static
│  ├─css
│  │      style.css
│  │
│  └─js
│          clips.js
│          licks.js
│          sidebar.js
│
├─templates
│  │  layout.html
│  │  sidebar.html
│  │
│  ├─account
│  │      index.html
│  │
│  ├─dev
│  │      index.html
│  │
│  └─music
│          clips.html
│          index.html
│          licks.html
│          playlist.html
│
├─utils
│    accountbook.py
│    music_util.py
└─   __init__.py