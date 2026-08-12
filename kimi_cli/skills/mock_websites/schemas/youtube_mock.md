# youtube_mock Schema

**Deploy order**: 57 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8057)
**Base URL**: `http://172.17.46.46:8057/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State inspect (raw)**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

Note: Port is dynamically assigned (vite `port: 0`). 8057 is the expected port at BASE_PORT=8000.

## Routes

| Path | Component |
|------|-----------|
| `/` | HomePage |
| `/watch/:videoId` | VideoPlayerPage |
| `/channel/:channelId` | ChannelPage |
| `/search?q=<query>` | SearchPage |
| `/subscriptions` | SubscriptionsPage |
| `/watch-later` | WatchLaterPage |
| `/history` | HistoryPage |
| `/liked` | LikedVideosPage |
| `/library` | LibraryPage |
| `/trending` | TrendingPage |
| `/playlist/:playlistId` | PlaylistPage |
| `/settings` | SettingsPage |
| `/go` | StateInspector (UI view) |

## State Schema

```
{
  user: {
    userId: string,                    // "user-1"
    displayName: string,               // "Alex Thompson"
    email: string,
    handle: string,                    // "@alexthompson"
    avatar: string,                    // URL
    subscribedChannels: string[],      // array of channelIds
    watchHistory: [                    // most recently watched first
      { videoId: string, watchedAt: ISO8601 }
    ],
    likedVideos: string[],             // array of videoIds
    watchLater: string[],              // array of videoIds
    playlists: string[]                // array of playlistIds
  },
  videos: [                            // 54 videos total
    {
      videoId: string,                 // "video-1" .. "video-54"
      title: string,
      description: string,
      channelId: string,
      channelName: string,
      channelAvatar: string,
      thumbnail: string,
      duration: string,                // "MM:SS" or "H:MM:SS"
      uploadDate: ISO8601,
      viewCount: number,
      likeCount: number,
      dislikeCount: number,
      category: string,                // "Gaming"|"Music"|"Tech"|"Cooking"|etc.
      tags: string[],
      videoUrl: string
    }
  ],
  channels: [                          // 16 channels (channel-1..channel-15 + user-1)
    {
      channelId: string,
      name: string,
      handle: string,
      avatar: string,
      banner: string,
      description: string,
      subscriberCount: number,
      videoCount: number,
      joinedDate: string,              // "YYYY-MM-DD"
      links: string[],
      videos: any[]
    }
  ],
  comments: {                          // keyed by videoId; populated for select videos
    [videoId]: [
      {
        commentId: string,
        videoId: string,
        userId: string,
        userName: string,
        userAvatar: string,
        text: string,
        timestamp: ISO8601,
        likeCount: number,
        dislikeCount: number,
        replies: Comment[],
        isPinned: boolean
      }
    ]
  },
  playlists: [                         // 5 user playlists
    {
      playlistId: string,              // "playlist-1".."playlist-5"
      name: string,
      description: string,
      creatorId: string,
      videoIds: string[],
      privacy: "Public"|"Private"|"Unlisted",
      createdDate: ISO8601,
      thumbnail: string
    }
  ],
  notifications: [                     // 4 default notifications
    {
      notificationId: string,
      type: "new_video",
      channelId: string,
      channelName: string,
      channelAvatar: string,
      videoId: string,
      videoTitle: string,
      videoThumbnail: string,
      timestamp: ISO8601,
      isRead: boolean
    }
  ],
  categories: string[],                // ["All","Gaming","Music","Live","News","Sports","Learning","Tech","Comedy","Cooking","Fitness","Travel"]
  settings: {
    autoplay: boolean,
    captions: boolean,
    subtitlesLang: string,
    theme: "light"|"dark",
    location: string,
    language: string,
    notifSubscriptions: boolean,
    notifRecommended: boolean,
    notifActivity: boolean,
    notifReplies: boolean,
    keepWatchHistory: boolean,
    keepSearchHistory: boolean
  }
}
```

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8057/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "userId": "user-1",
          "displayName": "Alex Thompson",
          "email": "alex.thompson@email.com",
          "handle": "@alexthompson",
          "avatar": "https://picsum.photos/100/100?random=current",
          "subscribedChannels": ["channel-1", "channel-2"],
          "watchHistory": [],
          "likedVideos": [],
          "watchLater": [],
          "playlists": ["playlist-1"]
        },
        "playlists": [
          {
            "playlistId": "playlist-1",
            "name": "My Playlist",
            "description": "",
            "creatorId": "user-1",
            "videoIds": ["video-1"],
            "privacy": "Public",
            "createdDate": "2024-01-01T00:00:00.000Z",
            "thumbnail": ""
          }
        ]
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Like a video | `user.likedVideos` — videoId added/removed |
| Subscribe to channel | `user.subscribedChannels` — channelId added/removed |
| Add to Watch Later | `user.watchLater` — videoId added/removed |
| Watch a video | `user.watchHistory` — `{videoId, watchedAt}` prepended |
| Clear watch history | `user.watchHistory` — array becomes `[]` |
| Create playlist | `playlists` — new playlist object appended; `user.playlists` — playlistId added |
| Add video to playlist | `playlists[i].videoIds` — videoId added |
| Remove video from playlist | `playlists[i].videoIds` — videoId removed |
| Delete playlist | `playlists` — object removed; `user.playlists` — playlistId removed |
| Mark notification read | `notifications[i].isRead` → `true` |
| Change setting | `settings.<key>` — value updated |
| Post comment | `comments[videoId]` — new comment object prepended |
